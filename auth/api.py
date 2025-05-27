#!/usr/bin/env python3
import re
import json
import time
import random
import string
import requests
import hashlib
import base64
import logging

logger = logging.getLogger("api_login")


class ApiLogin:
    def __init__(self, email, password, headers):
        """Initialize the Facebook API login handler with credentials"""
        self.email = email
        self.password = password

        # Use only essential headers for API login
        self.user_agent = headers.get("User-Agent", "")
        self.session = requests.Session()
        self.cookies = None
        self.debug_mode = True
        self.rate_limited = False

        # Generate a device ID that will be consistent for the same email
        email_hash = hashlib.md5(email.encode()).hexdigest()
        self.device_id = f"device_{email_hash[:16]}"

    def debug(self, message):
        """Print debug messages if debug mode is enabled"""
        if self.debug_mode:
            print(f"[DEBUG] {message}")
            logger.debug(message)

    def info(self, message):
        """Print info messages"""
        print(f"[*] {message}")
        logger.info(message)

    def success(self, message):
        """Print success messages"""
        print(f"[+] {message}")
        logger.info(f"SUCCESS: {message}")

    def error(self, message):
        """Print error messages"""
        print(f"[-] {message}")
        logger.error(message)

    def delay(self, min_sec=1.0, max_sec=3.0):
        """Add a random delay to simulate human interaction"""
        delay_time = random.uniform(min_sec, max_sec)
        time.sleep(delay_time)
        return delay_time

    def api_based_login(self):
        """
        Simplified API-based login method that focuses on reliability
        """
        try:
            self.info("Using API-based login approach...")

            # Clean session
            self.session = requests.Session()

            # Use more standard user agent
            standard_user_agent = "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.98 Mobile Safari/537.36"

            # API endpoint - use the main Facebook login endpoint instead of b-api
            api_url = "https://www.facebook.com/login/device-based/regular/login/?refsrc=deprecated&lwv=101"

            # Generate a device ID and other metadata for authenticity
            device_id = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=16)
            )

            # Generate a locale
            locale = "en_US"

            # Create API parameters with improved structure
            api_params = {"email": self.email, "pass": self.password, "login": "Log In"}

            # Try to fetch login form to get any required tokens
            self.debug("Fetching login page to extract tokens...")
            init_response = self.session.get(
                "https://www.facebook.com/login/",
                headers={
                    "User-Agent": standard_user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                },
                timeout=30,
            )

            # Look for important tokens in the page
            lsd_search = re.search(r'name="lsd" value="([^"]+)"', init_response.text)
            if lsd_search:
                api_params["lsd"] = lsd_search.group(1)
                self.debug(f"Found lsd token: {api_params['lsd']}")

            jazoest_search = re.search(
                r'name="jazoest" value="([^"]+)"', init_response.text
            )
            if jazoest_search:
                api_params["jazoest"] = jazoest_search.group(1)
                self.debug(f"Found jazoest token: {api_params['jazoest']}")

            # Look for additional tokens that might be needed
            token_searches = {
                "m_ts": r'name="m_ts" value="([^"]+)"',
                "li": r'name="li" value="([^"]+)"',
                "try_number": r'name="try_number" value="([^"]+)"',
                "unrecognized_tries": r'name="unrecognized_tries" value="([^"]+)"',
                "bi_xrwh": r'name="bi_xrwh" value="([^"]+)"',
                "submit": r'name="_fb_submit" value="([^"]+)"',
            }

            for key, pattern in token_searches.items():
                search = re.search(pattern, init_response.text)
                if search:
                    api_params[key] = search.group(1)
                    self.debug(f"Found {key}: {api_params[key]}")

            # Set API headers to mimic a real browser
            api_headers = {
                "User-Agent": standard_user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": "https://www.facebook.com/login/",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": "https://www.facebook.com",
                "Connection": "keep-alive",
                "Cache-Control": "max-age=0",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            }

            # Submit API request
            self.info("Sending API login request...")
            api_response = self.session.post(
                api_url,
                data=api_params,
                headers=api_headers,
                timeout=30,
                allow_redirects=True,
            )

            # Check login success - look for c_user cookie
            if "c_user" in self.session.cookies:
                self.success("API login successful!")
                return self.session, self.session.cookies

            # Try to access account page to confirm login
            account_response = self.session.get(
                "https://m.facebook.com/home.php",
                headers={
                    "User-Agent": standard_user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                },
                timeout=30,
            )

            # Check if we can access a page that requires login
            if "login" not in account_response.url and not any(
                term in account_response.text for term in ["login", "Log in", "Login"]
            ):
                self.success("Login successful validated via page access!")
                return self.session, self.session.cookies

            # Login failed
            self.error(
                "API login failed - invalid credentials or security check triggered"
            )
            return None, None

        except Exception as e:
            self.error(f"Error in api_based_login: {str(e)}")
            import traceback

            self.debug(f"Traceback: {traceback.format_exc()}")
            return None, None

    def mobile_api_login(self):
        """
        Alternative API login method using mobile endpoints
        """
        try:
            self.info("Using mobile API login approach...")

            # Clean session
            self.session = requests.Session()

            # Mobile API endpoint
            api_url = "https://m.facebook.com/login.php"

            # Generate random IDs
            device_id = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=16)
            )

            # First, visit the login page to get CSRF tokens
            self.debug("Fetching mobile login page for tokens...")
            initial_response = self.session.get(
                api_url,
                headers={
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                },
                timeout=30,
            )

            # Extract CSRF and other tokens
            form_data = {"email": self.email, "pass": self.password, "login": "Log In"}

            # Look for tokens
            lsd_search = re.search(r'name="lsd" value="([^"]+)"', initial_response.text)
            if lsd_search:
                form_data["lsd"] = lsd_search.group(1)

            jazoest_search = re.search(
                r'name="jazoest" value="([^"]+)"', initial_response.text
            )
            if jazoest_search:
                form_data["jazoest"] = jazoest_search.group(1)

            # Look for additional mobile-specific tokens
            for token in ["m_ts", "li", "try_number", "unrecognized_tries"]:
                search = re.search(
                    f'name="{token}" value="([^"]+)"', initial_response.text
                )
                if search:
                    form_data[token] = search.group(1)

            # Submit login
            self.info("Submitting mobile login request...")
            login_response = self.session.post(
                api_url,
                data=form_data,
                headers={
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Origin": "https://m.facebook.com",
                    "Referer": api_url,
                },
                timeout=30,
                allow_redirects=True,
            )

            # Check for successful login
            if "c_user" in self.session.cookies:
                self.success("Mobile API login successful!")
                return self.session, self.session.cookies

            # Try to access home page
            home_response = self.session.get(
                "https://m.facebook.com/home.php",
                headers={
                    "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                },
                timeout=30,
            )

            # Check if we're on the home page
            if "login" not in home_response.url:
                self.success("Mobile login validated via home page access!")
                return self.session, self.session.cookies

            # Login failed
            self.error("Mobile API login failed")
            return None, None

        except Exception as e:
            self.error(f"Error in mobile_api_login: {str(e)}")
            import traceback

            self.debug(f"Traceback: {traceback.format_exc()}")
            return None, None
