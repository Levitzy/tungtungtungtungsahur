#!/usr/bin/env python3
import re
import json
import time
import random
import string
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import urllib.parse
import hashlib
import base64


class FacebookLogin:
    def __init__(self, email, password, headers):
        """Initialize the Facebook login handler with credentials"""
        self.email = email
        self.password = password
        self.headers = headers
        self.session = requests.Session()
        self.user_agent = headers.get("User-Agent", "")
        self.cookies = None
        self.debug_mode = True  # Set to True for detailed output
        self.rate_limited = False

        # Generate a device ID that will be consistent for the same email
        email_hash = hashlib.md5(email.encode()).hexdigest()
        self.device_id = f"device_{email_hash[:16]}"

    def debug(self, message):
        """Print debug messages if debug mode is enabled"""
        if self.debug_mode:
            print(f"[DEBUG] {message}")

    def info(self, message):
        """Print info messages"""
        print(f"[*] {message}")

    def success(self, message):
        """Print success messages"""
        print(f"[+] {message}")

    def error(self, message):
        """Print error messages"""
        print(f"[-] {message}")

    def delay(self, min_sec=1.0, max_sec=3.0):
        """Add a random delay to simulate human interaction"""
        delay_time = random.uniform(min_sec, max_sec)
        time.sleep(delay_time)
        return delay_time

    def encode_payload(self, data):
        """Encode data in URL parameters"""
        payload = []
        for key, value in data.items():
            payload.append(f"{key}={urllib.parse.quote_plus(str(value))}")
        return "&".join(payload)

    def execute(self):
        """Execute the login process with multiple fallback methods"""
        # Try different login methods in order of stealth
        methods = [
            self.stealth_mobile_login,
            self.legacy_login_flow,
            self.direct_post_login,
            self.api_based_login,
            self.alternative_endpoint_login,
        ]

        for method in methods:
            try:
                method_name = method.__name__.replace("_", " ").title()
                self.info(f"Attempting login via {method_name}")
                session, cookies = method()
                if session and cookies:
                    return session, cookies

                # If we got rate limited, wait longer before trying the next method
                if self.rate_limited:
                    self.info("Detected rate limiting, waiting before next attempt...")
                    self.delay(15.0, 20.0)
                    self.rate_limited = False
                else:
                    self.delay(3.0, 5.0)

            except Exception as e:
                self.error(f"Error in {method.__name__}: {str(e)}")
                self.delay(2.0, 4.0)

        return None, None

    def is_rate_limited(self, response_text):
        """Check if the response indicates rate limiting"""
        rate_limit_phrases = [
            "You're Temporarily Blocked",
            "please try again later",
            "rate limited",
            "too many attempts",
            "too fast",
            "wait a few minutes",
            "try again later",
            "Something went wrong",
            "There was a problem",
            "Suspicious Activity",
            "security check",
            "We'll get back to you shortly",
            "technical problem",
        ]

        for phrase in rate_limit_phrases:
            if phrase.lower() in response_text.lower():
                self.rate_limited = True
                return True

        return False

    def extract_form_data(self, html_content):
        """Extract form data from HTML content"""
        soup = BeautifulSoup(html_content, "html.parser")
        form_data = {}

        # Try to find login form
        login_form = None
        form_selectors = [
            {"id": "login_form"},
            {"action": lambda x: x and "login" in x.lower()},
            {"method": "post"},
            {"id": lambda x: x and "login" in x.lower()},
            {"class": lambda x: x and "login" in x.lower()},
        ]

        for selector in form_selectors:
            login_form = soup.find("form", **selector)
            if login_form:
                self.debug(f"Found form with selector: {selector}")
                break

        if login_form:
            # Extract all input fields
            inputs = login_form.find_all("input")
            for input_field in inputs:
                if input_field.get("name"):
                    form_data[input_field.get("name")] = input_field.get("value", "")

        # Extract tokens from JavaScript
        token_patterns = {
            "fb_dtsg": [
                r'"(?:dtsg|fb_dtsg)":\s*"([^"]*)"',
                r'"(?:dtsg|fb_dtsg)":{"token":"(.*?)"',
                r'name="fb_dtsg" value="(.*?)"',
                r'{"dtsg(?:_ag)?":(?:[^}]*)"token":"([^"]*)"',
            ],
            "jazoest": [r'name="jazoest" value="(.*?)"', r'"jazoest":"([^"]*)"'],
            "lsd": [r'name="lsd" value="(.*?)"', r'"lsd":"([^"]*)"'],
            "__dyn": [r'"__dyn":"([^"]*)"'],
            "__csr": [r'"__csr":"([^"]*)"'],
            "__req": [r'"__req":"([^"]*)"'],
            "__a": [r'"__a":"([^"]*)"'],
            "__user": [r'"__user":"([^"]*)"'],
        }

        for token_name, patterns in token_patterns.items():
            for pattern in patterns:
                matches = re.search(pattern, html_content)
                if matches:
                    form_data[token_name] = matches.group(1)
                    break

        return form_data

    def stealth_mobile_login(self):
        """
        Stealth login method using mobile interface with modified approach
        This method tries to be as stealthy as possible
        """
        self.info("Using stealth mobile approach...")

        try:
            # Mobile login URL that triggers different authentication flow
            base_url = "https://m.facebook.com/"

            # First, visit homepage without triggering any suspicious behavior
            self.info("Visiting facebook homepage to gather cookies...")
            modified_headers = self.headers.copy()
            modified_headers["Accept"] = (
                "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
            )
            modified_headers["Cache-Control"] = "max-age=0"

            # Add some browser-like randomization
            if "Chrome" in self.user_agent:
                modified_headers["sec-ch-ua"] = (
                    '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"'
                )
                modified_headers["sec-ch-ua-mobile"] = (
                    "?1" if "Mobile" in self.user_agent else "?0"
                )
                modified_headers["sec-ch-ua-platform"] = (
                    '"Android"' if "Android" in self.user_agent else '"Windows"'
                )

            # 1. Visit homepage with a specific path that looks like normal browser navigation
            # The goal is to get initial cookies without triggering suspicion
            initial_path = "" if random.random() > 0.5 else f"?locale=en_US&_rdr"
            homepage_response = self.session.get(
                base_url + initial_path, headers=modified_headers, timeout=30
            )

            self.delay(2.0, 4.0)

            # Check if we're already rate limited
            if self.is_rate_limited(homepage_response.text):
                self.error("Rate limiting detected on homepage visit")
                return None, None

            # 2. Now visit a non-login page to establish more cookies, mimicking browsing behavior
            self.info("Establishing session cookies...")
            normal_pages = ["policies", "about", "help", "directory", "languages.php"]
            random_page = random.choice(normal_pages)

            # Set referer to homepage
            browse_headers = modified_headers.copy()
            browse_headers["Referer"] = base_url

            browse_response = self.session.get(
                base_url + random_page, headers=browse_headers, timeout=30
            )

            self.delay(1.5, 3.0)

            # 3. Now, visit the actual login page using a typical flow
            self.info("Getting login form...")
            login_headers = browse_headers.copy()
            login_headers["Referer"] = base_url + random_page

            # Sometimes Facebook uses different login paths based on locale/region
            login_paths = [
                "login",
                "login.php",
                "login/?privacy_mutation_token=",
                "login/device-based/regular/login/",
            ]

            login_path = random.choice(login_paths)
            login_response = self.session.get(
                base_url + login_path, headers=login_headers, timeout=30
            )

            if self.is_rate_limited(login_response.text):
                self.error("Rate limiting detected on login page")
                return None, None

            # 4. Extract login form data
            form_data = self.extract_form_data(login_response.text)
            self.debug(f"Found form data keys: {', '.join(form_data.keys())}")

            if not form_data:
                self.error("Could not extract form data")
                return None, None

            # 5. Add credentials to form data
            form_data["email"] = self.email
            form_data["pass"] = self.password

            # Add additional parameters that Facebook expects
            form_data["login_source"] = "comet_headerless_login"
            form_data["next"] = ""
            form_data["login"] = "1"

            # Add some random but expected parameters
            form_data["try_number"] = "0"
            form_data["unrecognized_tries"] = "0"
            form_data["prefill_contact_point"] = (
                self.email if random.random() > 0.5 else ""
            )
            form_data["prefill_source"] = random.choice(
                ["browser_dropdown", "browser_onload", ""]
            )
            form_data["prefill_type"] = "password"
            form_data["first_prefill_source"] = random.choice(
                ["browser_dropdown", "browser_onload", ""]
            )
            form_data["first_prefill_type"] = "password"
            form_data["had_cp_prefilled"] = "true" if random.random() > 0.5 else "false"
            form_data["had_password_prefilled"] = (
                "true" if random.random() > 0.5 else "false"
            )

            # Device-specific information to look more like a real device
            if "Android" in self.user_agent:
                form_data["bi_xrwh"] = "0"
                form_data["device_id"] = self.device_id

            # Generate unique identifiers for this request
            if "__a" not in form_data:
                form_data["__a"] = "1"
            if "__req" not in form_data:
                form_data["__req"] = random.choice(
                    string.ascii_lowercase + string.digits
                )
            if "__dyn" not in form_data:
                form_data["__dyn"] = ""
            if "__csr" not in form_data:
                form_data["__csr"] = ""

            # Delay to simulate typing credentials
            self.info("Entering credentials...")
            typing_delay = self.delay(3.0, 6.0)
            self.debug(f"Typed credentials in {typing_delay:.2f} seconds")

            # 6. Prepare submission headers
            submit_headers = login_headers.copy()
            submit_headers["Content-Type"] = "application/x-www-form-urlencoded"
            submit_headers["Origin"] = base_url.rstrip("/")
            submit_headers["Referer"] = login_response.url
            submit_headers["Accept"] = "*/*"
            submit_headers["Sec-Fetch-Site"] = "same-origin"
            submit_headers["Sec-Fetch-Mode"] = "cors"
            submit_headers["Sec-Fetch-Dest"] = "empty"

            # 7. Find the actual submission URL
            soup = BeautifulSoup(login_response.text, "html.parser")
            login_form = soup.find("form", id="login_form") or soup.find(
                "form", action=lambda x: x and "login" in x.lower()
            )

            submit_url = base_url + "login/device-based/regular/login/"
            if login_form and login_form.get("action"):
                action_url = login_form["action"]
                if action_url.startswith("http"):
                    submit_url = action_url
                elif action_url.startswith("/"):
                    submit_url = base_url.rstrip("/") + action_url
                else:
                    submit_url = base_url.rstrip("/") + "/" + action_url

            # 8. Submit the login form
            self.info(f"Submitting login form to {submit_url}...")

            # Think before clicking submit
            self.delay(1.5, 3.0)

            post_response = self.session.post(
                submit_url,
                data=form_data,
                headers=submit_headers,
                allow_redirects=True,
                timeout=30,
            )

            # 9. Check login success
            if "c_user" in self.session.cookies:
                self.success("Login successful! Found c_user cookie.")
                self.delay(1.0, 2.0)

                # Visit homepage to finalize the login and get all cookies
                self.info("Finalizing session...")
                home_response = self.session.get(
                    base_url + "home.php", headers=self.headers, timeout=30
                )

                return self.session, self.session.cookies

            elif "checkpoint" in post_response.url:
                self.error("Login requires verification/checkpoint")
                return None, None

            elif self.is_rate_limited(post_response.text):
                self.error("Rate limiting detected during login submission")
                return None, None

            else:
                self.debug("No clear success indicators found, checking response...")

                # Additional checks for success
                if any(
                    key in post_response.text.lower()
                    for key in ["home", "feed", "friends", "profile"]
                ):
                    self.success("Login appears successful based on page content")
                    return self.session, self.session.cookies

                # Check if we're still on the login page
                if "login" in post_response.url:
                    self.error("Still on login page after submission")
                    return None, None

                return None, None

        except Exception as e:
            self.error(f"Error in stealth_mobile_login: {str(e)}")
            return None, None

    def legacy_login_flow(self):
        """
        Legacy login flow using a different approach
        This uses a different login endpoint
        """
        try:
            self.info("Using legacy login flow...")
            base_url = "https://www.facebook.com/"

            # Clean session
            self.session = requests.Session()

            # Visit the homepage first
            initial_response = self.session.get(
                base_url, headers=self.headers, timeout=30
            )

            # Get cookies
            self.delay(2.0, 3.0)

            # Now visit login page
            login_response = self.session.get(
                base_url + "login.php", headers=self.headers, timeout=30
            )

            if self.is_rate_limited(login_response.text):
                self.error("Rate limiting detected on login page")
                return None, None

            # Extract form data
            form_data = self.extract_form_data(login_response.text)

            if not form_data:
                self.error("Could not extract form data")
                return None, None

            # Add credentials
            form_data["email"] = self.email
            form_data["pass"] = self.password
            form_data["login"] = "1"
            form_data["persistent"] = "1"  # Keep me logged in

            # Add delay for typing
            self.delay(2.0, 4.0)

            # Prepare submission headers
            submit_headers = self.headers.copy()
            submit_headers["Content-Type"] = "application/x-www-form-urlencoded"
            submit_headers["Origin"] = base_url.rstrip("/")
            submit_headers["Referer"] = login_response.url

            # Submit login
            self.info("Submitting legacy login form...")
            post_response = self.session.post(
                base_url + "login/device-based/regular/login/",
                data=form_data,
                headers=submit_headers,
                allow_redirects=True,
                timeout=30,
            )

            # Check login success
            if "c_user" in self.session.cookies:
                self.success("Legacy login successful!")
                return self.session, self.session.cookies

            # Additional checks
            if (
                "checkpoint" not in post_response.url
                and "login" not in post_response.url
            ):
                self.info("No redirect to login page, checking if login succeeded...")

                # Try to access home page
                home_response = self.session.get(
                    base_url + "me/", headers=self.headers, timeout=30
                )

                if "login" not in home_response.url:
                    self.success("Login verified via me page access")
                    return self.session, self.session.cookies

            return None, None

        except Exception as e:
            self.error(f"Error in legacy_login_flow: {str(e)}")
            return None, None

    def direct_post_login(self):
        """
        Direct POST login method without visiting login page first
        """
        try:
            self.info("Using direct POST login method...")
            base_url = "https://mobile.facebook.com/"

            # Clean session
            self.session = requests.Session()

            # Create a minimal form data set
            form_data = {
                "email": self.email,
                "pass": self.password,
                "login": "Log In",
                "lsd": hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
                "jazoest": "2" + "".join(str(ord(c)) for c in self.email[:5]),
                "uid": str(int(time.time() * 1000)),
                "next": "https://mobile.facebook.com/home.php",
                "locale": "en_US",
            }

            # Set headers
            direct_headers = self.headers.copy()
            direct_headers["Content-Type"] = "application/x-www-form-urlencoded"
            direct_headers["Origin"] = base_url.rstrip("/")
            direct_headers["Referer"] = base_url + "login"

            # Submit login directly
            self.info("Submitting direct login...")
            post_response = self.session.post(
                base_url + "login/device-based/login/async/",
                data=form_data,
                headers=direct_headers,
                allow_redirects=True,
                timeout=30,
            )

            # Check login success
            if "c_user" in self.session.cookies:
                self.success("Direct login successful!")
                return self.session, self.session.cookies

            # Try to access a protected page to verify login status
            self.info("Verifying login status...")
            verify_response = self.session.get(
                base_url + "me/", headers=self.headers, timeout=30
            )

            if "login" not in verify_response.url:
                self.success("Login verified!")
                return self.session, self.session.cookies

            return None, None

        except Exception as e:
            self.error(f"Error in direct_post_login: {str(e)}")
            return None, None

    def api_based_login(self):
        """
        API-based login method that mimics the mobile app
        """
        try:
            self.info("Using API-based login approach...")

            # Clean session
            self.session = requests.Session()

            # API endpoint
            api_url = "https://b-api.facebook.com/method/auth.login"

            # Generate a device ID
            device_id = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=16)
            )

            # Create API parameters
            api_params = {
                "access_token": "350685531728|62f8ce9f74b12f84c123cc23437a4a32",
                "format": "json",
                "sdk_version": "2",
                "email": self.email,
                "password": self.password,
                "locale": "en_US",
                "device_id": device_id,
                "generate_session_cookies": "1",
                "sig": hashlib.md5(
                    (self.email + self.password + device_id).encode()
                ).hexdigest(),
            }

            # Set API headers
            api_headers = {
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-G973F Build/RP1A.200720.012)",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "close",
                "Content-Type": "application/x-www-form-urlencoded",
                "x-fb-connection-type": "mobile.LTE",
                "x-fb-connection-quality": "EXCELLENT",
                "x-fb-device-group": "5120",
                "X-FB-Friendly-Name": "authenticate",
            }

            # Submit API request
            self.info("Sending API login request...")
            api_response = self.session.post(
                api_url, data=api_params, headers=api_headers, timeout=30
            )

            # Parse the response
            try:
                response_data = api_response.json()

                if "access_token" in response_data:
                    self.success("API login successful!")

                    # If session cookies are available, use them
                    if "session_cookies" in response_data:
                        for cookie in response_data["session_cookies"]:
                            self.session.cookies.set(
                                cookie["name"], cookie["value"], domain=".facebook.com"
                            )

                    return self.session, self.session.cookies

                elif "error_code" in response_data:
                    self.error(
                        f"API login error: {response_data.get('error_msg', 'Unknown error')}"
                    )

            except ValueError:
                self.error("Failed to parse API response")

            return None, None

        except Exception as e:
            self.error(f"Error in api_based_login: {str(e)}")
            return None, None

    def alternative_endpoint_login(self):
        """
        Final fallback using completely different login endpoints
        """
        try:
            self.info("Using alternative endpoint login...")

            # Try free basics Facebook (zero.facebook.com) which often has less security
            base_url = "https://0.facebook.com/"

            # Clean session
            self.session = requests.Session()

            # Visit homepage
            initial_response = self.session.get(
                base_url, headers=self.headers, timeout=30
            )

            self.delay(1.0, 3.0)

            # Visit login page
            login_response = self.session.get(
                base_url + "login", headers=self.headers, timeout=30
            )

            if self.is_rate_limited(login_response.text):
                self.error("Rate limiting detected on alternative login page")
                return None, None

            # Extract form data
            form_data = self.extract_form_data(login_response.text)

            if not form_data:
                self.error("Could not extract form data from alternative endpoint")
                return None, None

            # Add credentials
            form_data["email"] = self.email
            form_data["pass"] = self.password

            # Set submit headers
            submit_headers = self.headers.copy()
            submit_headers["Content-Type"] = "application/x-www-form-urlencoded"
            submit_headers["Origin"] = base_url.rstrip("/")
            submit_headers["Referer"] = login_response.url

            # Find form action URL
            soup = BeautifulSoup(login_response.text, "html.parser")
            login_form = soup.find("form")

            submit_url = base_url + "login"
            if login_form and login_form.get("action"):
                action_url = login_form["action"]
                if action_url.startswith("http"):
                    submit_url = action_url
                elif action_url.startswith("/"):
                    submit_url = base_url.rstrip("/") + action_url
                else:
                    submit_url = base_url.rstrip("/") + "/" + action_url

            # Submit login
            self.info(f"Submitting alternative login to {submit_url}...")
            post_response = self.session.post(
                submit_url,
                data=form_data,
                headers=submit_headers,
                allow_redirects=True,
                timeout=30,
            )

            # Check login success
            if "c_user" in self.session.cookies:
                self.success("Alternative login successful!")
                return self.session, self.session.cookies

            # Check if we can access a protected page
            check_response = self.session.get(
                base_url + "home.php", headers=self.headers, timeout=30
            )

            if "login" not in check_response.url:
                self.success("Alternative login verified!")
                return self.session, self.session.cookies

            return None, None

        except Exception as e:
            self.error(f"Error in alternative_endpoint_login: {str(e)}")
            return None, None


def facebook_login(email, password, headers):
    """
    Log into Facebook using multiple methods with fallbacks

    Args:
        email (str): Facebook email
        password (str): Facebook password
        headers (dict): HTTP headers to use for the request

    Returns:
        tuple: (requests.Session, list of cookies) if successful, (None, None) otherwise
    """
    # Initialize the login handler
    login_handler = FacebookLogin(email, password, headers)

    # Execute login process
    return login_handler.execute()
