#!/usr/bin/env python3
from flask import Flask, request, jsonify, make_response
import os
import json
import time
import hashlib
import threading
import ipaddress
from datetime import datetime, timedelta
from functools import wraps
from auth.login import facebook_login
from utils.headers import get_headers
from utils.user_agents import get_random_user_agent
from utils.cookie_manager import format_cookies_json, format_cookies_string

app = Flask(__name__)

# Configure API settings
API_CONFIG = {
    "max_requests_per_minute": 10,
    "max_failed_attempts": 5,
    "lockout_duration_minutes": 15,
    "cookie_expiry_days": 7,
    "enable_stored_credentials": True,
    "enable_rate_limiting": True,
    "enable_ip_blocking": True,
    "admin_token": os.environ.get(
        "ADMIN_TOKEN", hashlib.sha256(os.urandom(32)).hexdigest()[:16]
    ),
}

# In-memory storage for rate limiting and IP blocking
# In a production environment, consider using Redis or a database
request_counters = {}  # Format: {ip: {'count': 0, 'reset_time': timestamp}}
blocked_ips = {}  # Format: {ip: {'until': timestamp, 'reason': 'reason'}}
failed_logins = {}  # Format: {ip: {'count': 0, 'reset_time': timestamp}}
credentials_cache = (
    {}
)  # Format: {email_hash: {'cookies': {}, 'last_updated': timestamp}}


def rate_limit_decorator(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not API_CONFIG["enable_rate_limiting"]:
            return f(*args, **kwargs)

        ip = request.remote_addr
        current_time = time.time()

        # Check if IP is blocked
        if API_CONFIG["enable_ip_blocking"] and ip in blocked_ips:
            block_info = blocked_ips[ip]
            if current_time < block_info["until"]:
                remaining = int(block_info["until"] - current_time)
                return (
                    jsonify(
                        {
                            "status": "error",
                            "message": f"Access denied: {block_info['reason']}. Try again in {remaining} seconds.",
                        }
                    ),
                    429,
                )
            else:
                # Unblock if time has passed
                del blocked_ips[ip]

        # Initialize or reset counter if needed
        if (
            ip not in request_counters
            or current_time > request_counters[ip]["reset_time"]
        ):
            request_counters[ip] = {
                "count": 0,
                "reset_time": current_time + 60,  # Reset after 60 seconds
            }

        # Increment counter
        request_counters[ip]["count"] += 1

        # Check if limit exceeded
        if request_counters[ip]["count"] > API_CONFIG["max_requests_per_minute"]:
            # Block IP for excessive requests
            blocked_ips[ip] = {
                "until": current_time + (API_CONFIG["lockout_duration_minutes"] * 60),
                "reason": "Rate limit exceeded",
            }
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Rate limit exceeded. Please try again later.",
                    }
                ),
                429,
            )

        return f(*args, **kwargs)

    return decorated_function


def require_admin_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get("X-Admin-Token")
        if not token or token != API_CONFIG["admin_token"]:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Unauthorized: Invalid or missing admin token",
                    }
                ),
                401,
            )
        return f(*args, **kwargs)

    return decorated_function


def clean_expired_data():
    """Periodically clean expired data from memory caches"""
    current_time = time.time()

    # Clean expired credentials
    expired_credentials = []
    for email_hash, data in credentials_cache.items():
        expiry = data["last_updated"] + (API_CONFIG["cookie_expiry_days"] * 86400)
        if current_time > expiry:
            expired_credentials.append(email_hash)

    for email_hash in expired_credentials:
        del credentials_cache[email_hash]

    # Clean expired blocks
    expired_blocks = []
    for ip, block_info in blocked_ips.items():
        if current_time > block_info["until"]:
            expired_blocks.append(ip)

    for ip in expired_blocks:
        del blocked_ips[ip]

    # Schedule next cleaning
    threading.Timer(3600, clean_expired_data).start()  # Run every hour


@app.route("/api/login", methods=["POST", "GET"])
@rate_limit_decorator
def login():
    """Handle login requests with email and password, returns cookies directly.
    Accepts both POST with JSON body and GET with URL parameters."""
    ip = request.remote_addr
    current_time = time.time()

    # Get credentials from either POST JSON or GET parameters
    if request.method == "POST" and request.is_json:
        data = request.json
        email = data.get("email") if data else None
        password = data.get("password") if data else None
        use_cache = data.get("use_cache", False) if data else False
    else:
        # Extract from URL parameters
        email = request.args.get("email")
        password = request.args.get("password")
        use_cache = request.args.get("use_cache", "false").lower() == "true"

    # Validate input
    if not email or not password:
        return (
            jsonify({"status": "error", "message": "Email and password are required"}),
            400,
        )

    # Create hash for this email
    email_hash = hashlib.md5(email.encode()).hexdigest()[:8]

    # Check failed login attempts for this IP
    if ip in failed_logins and current_time < failed_logins[ip]["reset_time"]:
        if failed_logins[ip]["count"] >= API_CONFIG["max_failed_attempts"]:
            # Block IP for too many failed attempts
            blocked_ips[ip] = {
                "until": current_time + (API_CONFIG["lockout_duration_minutes"] * 60),
                "reason": "Too many failed login attempts",
            }
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Too many failed login attempts. Please try again later.",
                    }
                ),
                429,
            )
    else:
        # Reset failed login count if the time has passed
        failed_logins[ip] = {
            "count": 0,
            "reset_time": current_time + 3600,  # Reset after an hour
        }

    # Check if we have valid cached cookies
    if (
        API_CONFIG["enable_stored_credentials"]
        and email_hash in credentials_cache
        and current_time
        < credentials_cache[email_hash]["last_updated"]
        + (API_CONFIG["cookie_expiry_days"] * 86400)
    ):

        # Use cached cookies if they're not expired
        if use_cache:
            cookie_data = credentials_cache[email_hash]["cookies"]

            # Convert cookie data to string format
            from collections import namedtuple

            Cookie = namedtuple("Cookie", ["name", "value", "path"])

            cookie_objects = [
                Cookie(name=cookie["key"], value=cookie["value"], path=cookie["path"])
                for cookie in cookie_data
            ]

            cookie_string = format_cookies_string(cookie_objects)

            return jsonify(
                {
                    "status": "success",
                    "message": "Using cached session",
                    "cookies_json": cookie_data,
                    "cookies_string": cookie_string,
                    "cached": True,
                }
            )

    # Get random user agent and headers
    user_agent = get_random_user_agent()
    headers = get_headers(user_agent)

    # Attempt Facebook login
    session, cookies = facebook_login(email, password, headers)

    if session and cookies:
        # Format cookies for response
        cookie_data = format_cookies_json(cookies)
        cookie_string = format_cookies_string(cookies)

        # Cache the cookies
        credentials_cache[email_hash] = {
            "cookies": cookie_data,
            "last_updated": current_time,
        }

        # Reset failed login attempts for this IP
        if ip in failed_logins:
            failed_logins[ip]["count"] = 0

        return jsonify(
            {
                "status": "success",
                "message": "Login successful",
                "cookies_json": cookie_data,
                "cookies_string": cookie_string,
            }
        )
    else:
        # Increment failed login attempts
        failed_logins[ip]["count"] += 1

        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Login failed. Please check your credentials or try again later.",
                    "attempts_remaining": API_CONFIG["max_failed_attempts"]
                    - failed_logins[ip]["count"],
                }
            ),
            401,
        )


@app.route("/api/cookies/<email_hash>", methods=["GET"])
@rate_limit_decorator
def get_cookies(email_hash):
    """Retrieve stored cookies for a specific email hash"""
    current_time = time.time()

    # Check if cookies exist in cache
    if email_hash in credentials_cache and current_time < credentials_cache[email_hash][
        "last_updated"
    ] + (API_CONFIG["cookie_expiry_days"] * 86400):

        cookie_data = credentials_cache[email_hash]["cookies"]

        # Create cookie string
        from collections import namedtuple

        Cookie = namedtuple("Cookie", ["name", "value", "path"])

        cookie_objects = [
            Cookie(name=cookie["key"], value=cookie["value"], path=cookie["path"])
            for cookie in cookie_data
        ]

        cookie_string = format_cookies_string(cookie_objects)

        return jsonify(
            {
                "status": "success",
                "message": "Cookies retrieved successfully",
                "cookies_json": cookie_data,
                "cookies_string": cookie_string,
                "expires_in": int(
                    (
                        credentials_cache[email_hash]["last_updated"]
                        + (API_CONFIG["cookie_expiry_days"] * 86400)
                        - current_time
                    )
                    / 60
                ),  # Minutes
            }
        )

    return (
        jsonify({"status": "error", "message": "No cookies found for this email hash"}),
        404,
    )


@app.route("/api/status", methods=["GET"])
@rate_limit_decorator
def status():
    """Check API status"""
    total_cached = len(credentials_cache)
    total_blocked_ips = len(blocked_ips)

    return jsonify(
        {
            "status": "online",
            "service": "Facebook Login API",
            "version": "1.0.0",
            "uptime": int(time.time() - start_time),
            "cached_sessions": total_cached,
            "blocked_ips": total_blocked_ips,
            "rate_limiting": API_CONFIG["enable_rate_limiting"],
            "ip_blocking": API_CONFIG["enable_ip_blocking"],
        }
    )


@app.route("/api/admin/stats", methods=["GET"])
@require_admin_token
def admin_stats():
    """Get detailed API statistics (admin only)"""
    return jsonify(
        {
            "credentials_cache": {
                "count": len(credentials_cache),
                "entries": [
                    {
                        "email_hash": k,
                        "expires_in_hours": int(
                            (
                                v["last_updated"]
                                + (API_CONFIG["cookie_expiry_days"] * 86400)
                                - time.time()
                            )
                            / 3600
                        ),
                    }
                    for k, v in credentials_cache.items()
                ],
            },
            "blocked_ips": {
                "count": len(blocked_ips),
                "entries": [
                    {
                        "ip": k,
                        "reason": v["reason"],
                        "remaining_minutes": int((v["until"] - time.time()) / 60),
                    }
                    for k, v in blocked_ips.items()
                ],
            },
            "failed_logins": {
                "count": len(failed_logins),
                "entries": [
                    {
                        "ip": k,
                        "attempts": v["count"],
                        "resets_in_seconds": int(v["reset_time"] - time.time()),
                    }
                    for k, v in failed_logins.items()
                    if v["count"] > 0
                ],
            },
            "request_counters": {
                "count": len(request_counters),
                "entries": [
                    {
                        "ip": k,
                        "requests": v["count"],
                        "resets_in_seconds": int(v["reset_time"] - time.time()),
                    }
                    for k, v in request_counters.items()
                ],
            },
            "config": API_CONFIG,
        }
    )


@app.route("/api/admin/unblock/<ip>", methods=["POST"])
@require_admin_token
def admin_unblock(ip):
    """Unblock an IP address (admin only)"""
    try:
        # Validate IP format
        ipaddress.ip_address(ip)

        if ip in blocked_ips:
            del blocked_ips[ip]
            return jsonify(
                {"status": "success", "message": f"IP {ip} has been unblocked"}
            )
        else:
            return jsonify({"status": "warning", "message": f"IP {ip} was not blocked"})
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid IP address format"}), 400


@app.route("/api/admin/config", methods=["GET", "PUT"])
@require_admin_token
def admin_config():
    """Get or update API configuration (admin only)"""
    if request.method == "GET":
        return jsonify({"status": "success", "config": API_CONFIG})

    # Update config
    data = request.json
    if not data:
        return (
            jsonify({"status": "error", "message": "No configuration data provided"}),
            400,
        )

    # Update only allowed keys
    allowed_keys = [
        "max_requests_per_minute",
        "max_failed_attempts",
        "lockout_duration_minutes",
        "cookie_expiry_days",
        "enable_stored_credentials",
        "enable_rate_limiting",
        "enable_ip_blocking",
    ]

    for key in allowed_keys:
        if key in data:
            API_CONFIG[key] = data[key]

    return jsonify(
        {"status": "success", "message": "Configuration updated", "config": API_CONFIG}
    )


@app.route("/api/admin/clear-cache", methods=["POST"])
@require_admin_token
def admin_clear_cache():
    """Clear the credentials cache (admin only)"""
    credentials_cache.clear()
    return jsonify(
        {"status": "success", "message": "Credentials cache has been cleared"}
    )


@app.route("/", methods=["GET"])
def home():
    """Simple home page with usage information"""
    return """
    <html>
    <head>
        <title>Facebook Login API</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                color: #333;
            }
            h1 {
                color: #4267B2;
                border-bottom: 1px solid #ddd;
                padding-bottom: 10px;
            }
            code {
                background-color: #f5f5f5;
                padding: 2px 4px;
                border-radius: 4px;
                font-family: monospace;
            }
            pre {
                background-color: #f5f5f5;
                padding: 10px;
                border-radius: 4px;
                overflow-x: auto;
            }
            .endpoint {
                border-left: 4px solid #4267B2;
                padding-left: 15px;
                margin: 20px 0;
            }
            .warning {
                background-color: #fff3cd;
                padding: 10px;
                border-radius: 4px;
                border-left: 4px solid #ffc107;
            }
            .admin {
                background-color: #e8f5e9;
                padding: 10px;
                border-radius: 4px;
                border-left: 4px solid #4caf50;
            }
            .method {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 0.8em;
                color: white;
                font-weight: bold;
                margin-right: 8px;
            }
            .post {
                background-color: #4CAF50;
            }
            .get {
                background-color: #2196F3;
            }
        </style>
    </head>
    <body>
        <h1>Facebook Login API</h1>
        <p>This API provides a service to authenticate with Facebook and retrieve session cookies.</p>
        
        <div class="warning">
            <strong>Note:</strong> This API is for development and testing purposes only. 
            Be responsible and respect Facebook's Terms of Service.
        </div>
        
        <h2>Available Endpoints</h2>
        
        <div class="endpoint">
            <h3>Login</h3>
            <p><span class="method post">POST</span> <span class="method get">GET</span> <code>/api/login</code></p>
            <p>Authenticates with Facebook using the provided credentials and returns cookies directly.</p>
            
            <h4>Method 1: POST with JSON body</h4>
            <pre>
# Request:
POST /api/login
Content-Type: application/json

{
  "email": "your_email@example.com",
  "password": "your_password",
  "use_cache": true  // Optional: use cached session if available
}
            </pre>
            
            <h4>Method 2: GET with URL parameters</h4>
            <pre>
# Request:
GET /api/login?email=your_email@example.com&password=your_password&use_cache=true
            </pre>
            
            <h4>Response Format (Success):</h4>
            <pre>
{
  "status": "success",
  "message": "Login successful",
  "cookies_json": [
    { "key": "cookie_name", "value": "cookie_value", "domain": "facebook.com", "path": "/", ... },
    ...
  ],
  "cookies_string": "cookie_name=cookie_value; cookie_name2=cookie_value2; ..."
}
            </pre>
        </div>
        
        <div class="endpoint">
            <h3>Get Cookies</h3>
            <p><span class="method get">GET</span> <code>/api/cookies/{email_hash}</code></p>
            <p>Retrieves stored cookies for a specific email hash.</p>
            <h4>Response Format (Success):</h4>
            <pre>
{
  "status": "success",
  "message": "Cookies retrieved successfully",
  "cookies_json": [
    { "key": "cookie_name", "value": "cookie_value", "domain": "facebook.com", "path": "/", ... },
    ...
  ],
  "cookies_string": "cookie_name=cookie_value; cookie_name2=cookie_value2; ...",
  "expires_in": 10080  // Minutes until cookies expire
}
            </pre>
        </div>
        
        <div class="endpoint">
            <h3>Status</h3>
            <p><span class="method get">GET</span> <code>/api/status</code></p>
            <p>Returns the current API status.</p>
        </div>
        
        <div class="admin">
            <h3>Admin Endpoints</h3>
            <p>These endpoints require the X-Admin-Token header with a valid admin token.</p>
            <ul>
                <li><code>GET /api/admin/stats</code> - Get detailed API statistics</li>
                <li><code>POST /api/admin/unblock/{ip}</code> - Unblock an IP address</li>
                <li><code>GET/PUT /api/admin/config</code> - Get or update API configuration</li>
                <li><code>POST /api/admin/clear-cache</code> - Clear the credentials cache</li>
            </ul>
        </div>
        
        <h2>Example Usage</h2>
        
        <h3>Example 1: URL Method (Simple)</h3>
        <pre>
# Using a web browser or simple GET request:
http://localhost:5000/api/login?email=your_email@example.com&password=your_password
        </pre>
        
        <h3>Example 2: Python with JSON Method</h3>
        <pre>
import requests
import json

url = "http://localhost:5000/api/login"
data = {
    "email": "your_email@example.com",
    "password": "your_password"
}

response = requests.post(url, json=data)
result = response.json()

if result["status"] == "success":
    print("Login successful!")
    
    # You can use the cookies_string directly with requests
    cookies_string = result["cookies_string"]
    print(f"Cookie string: {cookies_string}")
    
    # Or you can use the detailed JSON format for more control
    cookies_json = result["cookies_json"]
    print(f"Retrieved {len(cookies_json)} cookies")
    
    # Example: Create a session with these cookies
    session = requests.Session()
    for cookie in cookies_json:
        session.cookies.set(cookie["key"], cookie["value"], 
                          domain=cookie["domain"], path=cookie["path"])
    
    # Use the session for authenticated requests
    profile = session.get("https://www.facebook.com/me")
else:
    print(f"Login failed: {result['message']}")
        </pre>
    </body>
    </html>
    """


# Record start time for uptime tracking
start_time = time.time()

# Start cleanup task
cleanup_thread = threading.Timer(3600, clean_expired_data)
cleanup_thread.daemon = True
cleanup_thread.start()

if __name__ == "__main__":
    # Get port from environment variable or use default 5000
    port = int(os.environ.get("PORT", 5000))

    # Output admin token to console
    print(f"\n{'='*60}")
    print(f" Facebook Login API Server")
    print(f"{'='*60}")
    print(f" Admin Token: {API_CONFIG['admin_token']}")
    print(f" Use this token in the X-Admin-Token header for admin endpoints")
    print(f"{'='*60}\n")

    # Run the app
    app.run(host="0.0.0.0", port=port, debug=False)
