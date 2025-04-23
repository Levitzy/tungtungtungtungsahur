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


class MobileLogin:
    def __init__(self, email, password, headers):
        """Initialize the Facebook mobile login handler with credentials"""
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

    def stealth_mobile_login(self):
        """
        Improved stealth login method using mobile interface
        """
        self.info("Using stealth mobile approach...")

        try:
            # Use mbasic.facebook.com instead of m.facebook.com - often has fewer restrictions
            base_url = "https://mbasic.facebook.com/"

            # First, visit homepage without triggering any suspicious behavior
            self.info("Visiting facebook homepage to gather cookies...")
            modified_headers = self.headers.copy()

            # Simplify headers to reduce fingerprinting
            modified_headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            # 1. Visit homepage without any params - simpler is better for stealth
            homepage_response = self.session.get(
                base_url, headers=modified_headers, timeout=30
            )

            self.delay(1.0, 2.0)  # Shorter delay to avoid timeouts

            # Check if we're already rate limited
            if self.is_rate_limited(homepage_response.text):
                self.error("Rate limiting detected on homepage visit")
                return None, None

            # 2. Now visit login page directly with cookies established
            self.info("Getting login form...")
            login_headers = modified_headers.copy()
            login_headers["Referer"] = base_url

            # Use consistent simple login path for mbasic
            login_url = base_url + "login.php"

            login_response = self.session.get(
                login_url, headers=login_headers, timeout=30
            )

            if self.is_rate_limited(login_response.text):
                self.error("Rate limiting detected on login page")
                return None, None

            # 3. Extract login form data
            form_data = self.extract_form_data(login_response.text)

            if not form_data:
                self.error("Could not extract form data, trying backup method")
                # Backup form data extraction - create minimal required set
                form_data = {
                    "email": self.email,
                    "pass": self.password,
                    "login": "Log In",
                }
            else:
                self.debug(f"Found form data keys: {', '.join(form_data.keys())}")
                # Add credentials to form data
                form_data["email"] = self.email
                form_data["pass"] = self.password

            # Keep form data minimal - this is key for mbasic login
            if "lsd" not in form_data:
                form_data["lsd"] = ""

            # Check if additional parameters exist in the form and keep them
            # For mbasic.facebook.com, it's best to use only what's directly in the form

            # Add delay to simulate typing credentials
            self.info("Entering credentials...")
            typing_delay = self.delay(1.0, 2.0)  # Shorter delay
            self.debug(f"Typed credentials in {typing_delay:.2f} seconds")

            # 4. Prepare submission headers - keep these minimal
            submit_headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Content-Type": "application/x-www-form-urlencoded",
                "Origin": base_url.rstrip("/"),
                "Referer": login_response.url,
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            # 5. Find the actual submission URL from the form
            soup = BeautifulSoup(login_response.text, "html.parser")
            login_form = soup.find("form", id="login_form") or soup.find(
                "form", action=lambda x: x and "login" in x.lower()
            )

            submit_url = login_url
            if login_form and login_form.get("action"):
                action_url = login_form["action"]
                if action_url.startswith("http"):
                    submit_url = action_url
                elif action_url.startswith("/"):
                    submit_url = base_url.rstrip("/") + action_url
                else:
                    submit_url = base_url.rstrip("/") + "/" + action_url

            # 6. Submit the login form
            self.info(f"Submitting login form to {submit_url}...")

            # Short pause before clicking submit
            self.delay(0.5, 1.0)

            post_response = self.session.post(
                submit_url,
                data=form_data,
                headers=submit_headers,
                allow_redirects=True,
                timeout=30,
            )

            # 7. Check login success
            if "c_user" in self.session.cookies:
                self.success("Login successful! Found c_user cookie.")

                # Visit homepage to finalize the login and get all cookies
                self.info("Finalizing session...")
                self.delay(0.5, 1.0)

                home_response = self.session.get(
                    base_url, headers=modified_headers, timeout=30
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
                success_indicators = [
                    "home",
                    "feed",
                    "friends",
                    "profile",
                    "notifications",
                    "messages",
                ]
                if any(key in post_response.text.lower() for key in success_indicators):
                    self.success("Login appears successful based on page content")
                    return self.session, self.session.cookies

                # Check if we're still on the login page
                if "login" in post_response.url or "Log In" in post_response.text:
                    self.error("Still on login page after submission")
                    return None, None

                # If no clear indication, but we're not on login page, consider it a success
                if (
                    "login" not in post_response.url
                    and "Log In" not in post_response.text
                ):
                    self.success("Login appears successful (not on login page)")
                    return self.session, self.session.cookies

                return None, None

        except Exception as e:
            self.error(f"Error in stealth_mobile_login: {str(e)}")
            return None, None

    def mobile_direct_login(self):
        """
        Alternative mobile login method that uses direct POST
        """
        self.info("Using mobile direct login approach...")

        try:
            # Clean session
            self.session = requests.Session()

            # Use free basics Facebook which often has less restriction
            base_url = "https://0.facebook.com/"

            # Very minimal headers to avoid detection
            simple_headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            # Visit the homepage to establish cookies
            initial_response = self.session.get(
                base_url, headers=simple_headers, timeout=30
            )

            self.delay(0.8, 1.5)

            # Visit login page to get form data
            login_response = self.session.get(
                base_url + "login.php", headers=simple_headers, timeout=30
            )

            if self.is_rate_limited(login_response.text):
                self.error("Rate limiting detected on mobile login page")
                return None, None

            # Extract form data
            form_data = self.extract_form_data(login_response.text)

            if not form_data:
                self.error("Could not extract form data, creating minimal set")
                form_data = {
                    "email": self.email,
                    "pass": self.password,
                    "login": "Log In",
                }
            else:
                # Add credentials
                form_data["email"] = self.email
                form_data["pass"] = self.password
                if "login" not in form_data:
                    form_data["login"] = "Log In"

            # Add delay to simulate typing
            self.delay(1.0, 2.0)

            # Set submit headers - keep very simple
            submit_headers = simple_headers.copy()
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

            submit_url = base_url + "login.php"
            if login_form and login_form.get("action"):
                action_url = login_form["action"]
                if action_url.startswith("http"):
                    submit_url = action_url
                elif action_url.startswith("/"):
                    submit_url = base_url.rstrip("/") + action_url
                else:
                    submit_url = base_url.rstrip("/") + "/" + action_url

            # Submit login
            self.info(f"Submitting mobile direct login to {submit_url}...")
            post_response = self.session.post(
                submit_url,
                data=form_data,
                headers=submit_headers,
                allow_redirects=True,
                timeout=30,
            )

            # Check login success
            if "c_user" in self.session.cookies:
                self.success("Mobile direct login successful!")
                return self.session, self.session.cookies

            # Additional checks
            if (
                "checkpoint" not in post_response.url
                and "login" not in post_response.url
            ):
                self.info("No redirect to login page, checking if login succeeded...")

                # Try to access home page
                home_response = self.session.get(
                    base_url, headers=simple_headers, timeout=30
                )

                if (
                    "login" not in home_response.url
                    and "c_user" in self.session.cookies
                ):
                    self.success("Login verified via home page access")
                    return self.session, self.session.cookies

                # Check if any success indicator is in the response
                success_indicators = ["home", "feed", "friends", "profile", "welcome"]
                if any(
                    indicator in home_response.text.lower()
                    for indicator in success_indicators
                ):
                    self.success("Login verified via content checks")
                    return self.session, self.session.cookies

            return None, None

        except Exception as e:
            self.error(f"Error in mobile_direct_login: {str(e)}")
            return None, None
