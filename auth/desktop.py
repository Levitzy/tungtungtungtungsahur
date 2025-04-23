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


class DesktopLogin:
    def __init__(self, email, password, headers):
        """Initialize the Facebook desktop login handler with credentials"""
        self.email = email
        self.password = password
        self.headers = headers
        self.session = requests.Session()
        self.user_agent = headers.get("User-Agent", "")
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

    def standard_desktop_login(self):
        """
        Standard desktop login flow using www.facebook.com
        """
        self.info("Using standard desktop login flow...")

        try:
            # Desktop login URL
            base_url = "https://www.facebook.com/"

            # Clean session
            self.session = requests.Session()

            # Use simplified headers to avoid detection
            desktop_headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Cache-Control": "max-age=0",
            }

            # Visit the homepage first to get initial cookies
            initial_response = self.session.get(
                base_url, headers=desktop_headers, timeout=30
            )

            # Get cookies and delay
            self.delay(1.0, 2.0)

            # Now visit login page
            login_headers = desktop_headers.copy()
            login_headers["Referer"] = base_url

            # Go directly to the login page without redirects
            login_response = self.session.get(
                base_url + "login.php",
                headers=login_headers,
                timeout=30,
                allow_redirects=True,  # Allow redirects but follow them for accurate form data
            )

            if self.is_rate_limited(login_response.text):
                self.error("Rate limiting detected on login page")
                return None, None

            # Extract form data
            form_data = self.extract_form_data(login_response.text)

            if not form_data:
                self.error("Could not extract form data, creating minimal set")
                # Create minimal fallback form data
                form_data = {
                    "email": self.email,
                    "pass": self.password,
                    "login": "1",
                    "lsd": hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
                    "jazoest": "2" + "".join(str(ord(c)) for c in self.email[:5]),
                }
            else:
                # Add credentials
                form_data["email"] = self.email
                form_data["pass"] = self.password
                form_data["login"] = "1"
                # Don't add extra fields that might not be needed

            # Add the timezone info if needed, nothing else
            form_data["timezone"] = (
                str(int(-time.timezone / 60))
                if "timezone" in login_response.text
                else "240"
            )

            # Add delay for typing - shorter is better to avoid timeouts
            self.delay(1.5, 2.5)

            # Prepare submission headers
            submit_headers = login_headers.copy()
            submit_headers["Content-Type"] = "application/x-www-form-urlencoded"
            submit_headers["Origin"] = base_url.rstrip("/")
            submit_headers["Referer"] = login_response.url

            # Find the form action
            soup = BeautifulSoup(login_response.text, "html.parser")
            login_form = (
                soup.find("form", id="login_form")
                or soup.find("form", action=lambda x: x and "login" in x.lower())
                or soup.find("form")
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

            # Submit login
            self.info(f"Submitting desktop login form to {submit_url}...")

            # Brief pause before clicking submit
            self.delay(0.5, 1.0)

            post_response = self.session.post(
                submit_url,
                data=form_data,
                headers=submit_headers,
                allow_redirects=True,
                timeout=30,
            )

            # Check login success
            if "c_user" in self.session.cookies:
                self.success("Desktop login successful!")
                return self.session, self.session.cookies

            # Additional checks
            if (
                "checkpoint" not in post_response.url
                and "login" not in post_response.url
            ):
                self.info("No redirect to login page, checking if login succeeded...")

                # Try to access protected page
                me_response = self.session.get(
                    base_url + "me/", headers=desktop_headers, timeout=30
                )

                if "login" not in me_response.url:
                    self.success("Desktop login verified via me page access")
                    return self.session, self.session.cookies

                # Check for success indicators in content
                success_indicators = ["home", "feed", "profile", "friends", "messages"]
                if any(
                    indicator in post_response.text.lower()
                    for indicator in success_indicators
                ):
                    self.success("Desktop login verified via content checks")
                    return self.session, self.session.cookies

            return None, None

        except Exception as e:
            self.error(f"Error in standard_desktop_login: {str(e)}")
            return None, None

    def alternative_desktop_login(self):
        """
        Alternative desktop login flow using a different approach
        """
        self.info("Using alternative desktop login approach...")

        try:
            # Use Facebook lite version which often has fewer restrictions
            base_url = "https://facebook.com/lite/"

            # Clean session
            self.session = requests.Session()

            # Simple headers to minimize fingerprinting
            alt_headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            # Visit the homepage to get cookies
            initial_response = self.session.get(
                base_url, headers=alt_headers, timeout=30
            )

            self.delay(0.8, 1.5)

            # Visit login page
            login_url = "https://facebook.com/login.php"
            login_headers = alt_headers.copy()
            login_headers["Referer"] = base_url

            login_response = self.session.get(
                login_url, headers=login_headers, timeout=30
            )

            if self.is_rate_limited(login_response.text):
                self.error("Rate limiting detected on alternative login page")
                return None, None

            # Extract form data from the login page
            form_data = self.extract_form_data(login_response.text)

            if not form_data:
                self.error("Could not extract form data, creating minimal version")
                # Create minimal form data that works for many FB versions
                form_data = {
                    "email": self.email,
                    "pass": self.password,
                    "login": "Log In",
                    "lsd": hashlib.md5(str(time.time()).encode()).hexdigest()[:8],
                }
            else:
                # Add credentials
                form_data["email"] = self.email
                form_data["pass"] = self.password
                # Ensure login parameter exists
                if "login" not in form_data:
                    form_data["login"] = "Log In"

            # Add delay for typing
            self.delay(1.0, 2.0)

            # Prepare submission headers
            submit_headers = alt_headers.copy()
            submit_headers["Content-Type"] = "application/x-www-form-urlencoded"
            submit_headers["Origin"] = "https://facebook.com"
            submit_headers["Referer"] = login_response.url

            # Find the form action
            soup = BeautifulSoup(login_response.text, "html.parser")
            login_form = (
                soup.find("form", id="login_form")
                or soup.find("form", action=lambda x: x and "login" in x.lower())
                or soup.find("form")
            )

            submit_url = "https://facebook.com/login/device-based/regular/login/"
            if login_form and login_form.get("action"):
                action_url = login_form["action"]
                if action_url.startswith("http"):
                    submit_url = action_url
                elif action_url.startswith("/"):
                    submit_url = "https://facebook.com" + action_url
                else:
                    submit_url = "https://facebook.com/" + action_url

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
                self.success("Alternative desktop login successful!")
                return self.session, self.session.cookies

            # Check if we're still on the login page
            if (
                "login" not in post_response.url
                and "c_user" not in self.session.cookies
            ):
                # Try to access home page to verify login
                home_response = self.session.get(
                    "https://facebook.com/", headers=alt_headers, timeout=30
                )

                if "c_user" in self.session.cookies:
                    self.success("Login successful after home page visit!")
                    return self.session, self.session.cookies

                # Check for success indicators in content
                success_indicators = ["home", "feed", "profile", "friends", "messages"]
                if any(
                    indicator in home_response.text.lower()
                    for indicator in success_indicators
                ):
                    self.success("Login appears successful based on content!")
                    return self.session, self.session.cookies

            return None, None

        except Exception as e:
            self.error(f"Error in alternative_desktop_login: {str(e)}")
            return None, None
