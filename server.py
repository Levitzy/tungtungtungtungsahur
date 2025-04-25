#!/usr/bin/env python3
from flask import Flask, request, jsonify, send_from_directory, render_template
from flask_cors import CORS
import os
import json
import time
import logging
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler("fb_auth.log"),  # Log to file
    ],
)
logger = logging.getLogger("fb_auth")

# Import the facebook_login function from auth/login.py
from auth.login import facebook_login
from utils.headers import get_headers
from utils.user_agents import get_random_user_agent

# Create Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)  # Enable CORS for all routes

# Create necessary directories if they don't exist
os.makedirs("static", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)
os.makedirs("sessions", exist_ok=True)
os.makedirs("logs", exist_ok=True)


def generate_session_id():
    """Generate a unique session ID based on timestamp and random values"""
    import random
    import string
    import hashlib

    timestamp = str(time.time())
    random_string = "".join(random.choices(string.ascii_letters + string.digits, k=16))
    session_id = hashlib.md5((timestamp + random_string).encode()).hexdigest()
    return session_id


def save_session(session_id, email, cookies, user_agent):
    """Save session data to a file"""
    session_data = {
        "session_id": session_id,
        "email": email,
        "cookies": [
            {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path,
            }
            for cookie in cookies
        ],
        "user_agent": user_agent,
        "created_at": datetime.now().isoformat(),
        "last_used": datetime.now().isoformat(),
    }

    with open(f"sessions/{session_id}.json", "w") as f:
        json.dump(session_data, f, indent=4)

    return session_data


def get_session(session_id):
    """Get session data from file"""
    try:
        with open(f"sessions/{session_id}.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def update_session_timestamp(session_id):
    """Update the last_used timestamp of a session"""
    session_data = get_session(session_id)
    if session_data:
        session_data["last_used"] = datetime.now().isoformat()
        with open(f"sessions/{session_id}.json", "w") as f:
            json.dump(session_data, f, indent=4)


# Routes for the web interface
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


# API routes
@app.route("/api/login", methods=["POST"])
def api_login():
    """API endpoint for Facebook login"""
    data = request.get_json()

    logger.info("Login request received")

    if not data:
        logger.warning("No data provided in login request")
        return jsonify({"success": False, "message": "No data provided"}), 400

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        logger.warning("Missing email or password in login request")
        return (
            jsonify({"success": False, "message": "Email and password are required"}),
            400,
        )

    # Get a random user agent and headers
    user_agent = get_random_user_agent()
    headers = get_headers(user_agent)

    logger.info(f"Attempting login for {email} with user agent: {user_agent[:30]}...")

    # Perform the login
    try:
        session, cookies = facebook_login(email, password, headers)

        if session and cookies:
            # Generate a session ID and save the session
            session_id = generate_session_id()
            session_data = save_session(session_id, email, cookies, user_agent)

            logger.info(f"Login successful for {email}, session ID: {session_id}")

            # Create list of cookies for the response
            cookie_list = [
                {"name": cookie.name, "value": cookie.value}
                for cookie in cookies
                if cookie.name in ["c_user", "xs", "fr", "datr"]
            ]

            logger.debug(f"Returning {len(cookie_list)} cookies to client")

            # Return success with session ID and essential cookies
            return jsonify(
                {
                    "success": True,
                    "message": "Login successful",
                    "session_id": session_id,
                    "email": email,
                    "cookies": cookie_list,
                }
            )
        else:
            logger.warning(
                f"Login failed for {email} - invalid credentials or account requires verification"
            )
            return (
                jsonify(
                    {
                        "success": False,
                        "message": "Login failed. Invalid credentials or account requires verification",
                    }
                ),
                401,
            )

    except Exception as e:
        logger.error(f"Error during login for {email}: {str(e)}")
        logger.error(traceback.format_exc())
        return (
            jsonify(
                {
                    "success": False,
                    "message": f"Error during login: {str(e)}",
                    "error_details": traceback.format_exc(),
                }
            ),
            500,
        )


@app.route("/api/health", methods=["GET"])
def health_check():
    """API health check endpoint"""
    try:
        # Check basic functionality
        if os.path.exists("sessions"):
            return jsonify(
                {
                    "status": "healthy",
                    "message": "API is functioning correctly",
                    "environment": {
                        "platform": platform.platform(),
                        "python_version": platform.python_version(),
                        "server_time": datetime.now().isoformat(),
                    },
                }
            )
        else:
            return (
                jsonify(
                    {
                        "status": "degraded",
                        "message": "Sessions directory not accessible",
                    }
                ),
                500,
            )
    except Exception as e:
        return jsonify({"status": "unhealthy", "message": str(e)}), 500


@app.route("/api/sessions", methods=["GET"])
def list_sessions():
    """List all active sessions"""
    sessions = []

    for filename in os.listdir("sessions"):
        if filename.endswith(".json"):
            session_id = filename[:-5]  # Remove .json extension
            session_data = get_session(session_id)
            if session_data:
                # Add only necessary info to the response
                sessions.append(
                    {
                        "session_id": session_id,
                        "email": session_data.get("email"),
                        "created_at": session_data.get("created_at"),
                        "last_used": session_data.get("last_used"),
                    }
                )

    return jsonify({"success": True, "sessions": sessions})


@app.route("/api/sessions/<session_id>", methods=["GET"])
def get_session_data(session_id):
    """Get data for a specific session"""
    session_data = get_session(session_id)

    if session_data:
        update_session_timestamp(session_id)
        return jsonify({"success": True, "session": session_data})
    else:
        return jsonify({"success": False, "message": "Session not found"}), 404


@app.route("/api/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    """Delete a session"""
    session_file = f"sessions/{session_id}.json"

    if os.path.exists(session_file):
        os.remove(session_file)
        return jsonify({"success": True, "message": "Session deleted"})
    else:
        return jsonify({"success": False, "message": "Session not found"}), 404


@app.route("/api/cookies/<session_id>", methods=["GET"])
def get_cookies(session_id):
    """Get cookies for a specific session"""
    session_data = get_session(session_id)

    if session_data and "cookies" in session_data:
        return jsonify({"success": True, "cookies": session_data["cookies"]})
    else:
        return (
            jsonify({"success": False, "message": "Session or cookies not found"}),
            404,
        )


@app.route("/api/cookies/<session_id>/export", methods=["GET"])
def export_cookies(session_id):
    """Export cookies in requested format"""
    format_type = request.args.get("format", "json")
    session_data = get_session(session_id)

    if not session_data or "cookies" not in session_data:
        return (
            jsonify({"success": False, "message": "Session or cookies not found"}),
            404,
        )

    cookies = session_data["cookies"]

    # Format cookies properly
    formatted_cookies = []
    now = datetime.now().isoformat() + "Z"

    for cookie in cookies:
        # Create new cookie entry with proper format
        cookie_entry = {
            "key": cookie.get("name", cookie.get("key", "")),
            "value": cookie.get("value", ""),
            "domain": cookie.get("domain", "facebook.com"),
            "path": cookie.get("path", "/"),
            "hostOnly": cookie.get("hostOnly", False),
            "creation": cookie.get("creation", now),
            "lastAccessed": cookie.get("lastAccessed", now),
        }
        formatted_cookies.append(cookie_entry)

    if format_type == "json":
        # Return direct JSON array without success wrapper
        return (
            json.dumps(formatted_cookies, indent=3),
            200,
            {"Content-Type": "application/json"},
        )

    elif format_type == "netscape":
        # Netscape format (for browsers)
        netscape_cookies = []
        for cookie in formatted_cookies:
            domain = cookie.get("domain", ".facebook.com")
            if not domain.startswith("."):
                domain = "." + domain
            flag = "TRUE"
            path = cookie.get("path", "/")
            secure = "TRUE"
            expiry = int(time.time()) + 86400 * 30  # 30 days
            name = cookie.get("key", "")
            value = cookie.get("value", "")

            netscape_cookies.append(
                f"{domain}\t{flag}\t{path}\t{secure}\t{expiry}\t{name}\t{value}"
            )

        netscape_str = "\n".join(netscape_cookies)
        return netscape_str, 200, {"Content-Type": "text/plain"}

    elif format_type == "string":
        # Simple cookie string format
        cookie_str = "; ".join(
            [f"{c.get('key')}={c.get('value')}" for c in formatted_cookies]
        )
        return cookie_str, 200, {"Content-Type": "text/plain"}

    else:
        return jsonify({"success": False, "message": "Invalid format specified"}), 400


@app.route("/logs", methods=["GET"])
def view_logs():
    """View application logs - DEVELOPMENT ONLY"""
    try:
        with open("fb_auth.log", "r") as f:
            log_content = f.read()
        return log_content, 200, {"Content-Type": "text/plain"}
    except Exception as e:
        return f"Error retrieving logs: {str(e)}", 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "False").lower() == "true"

    logger.info(f"Starting server on port {port} with debug={debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)
