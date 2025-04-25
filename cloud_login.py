#!/usr/bin/env python3
import requests
import time
import random
import logging
import json
import re

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("cloud_login")


class CloudLogin:
    """
    Simplified login method specifically for cloud environments like Render
    where Facebook might apply stricter security measures
    """

    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.session = requests.Session()

        # Configure longer timeouts
        self.timeout = 60

        # Configure retries
        self.max_retries = 3

        # Setup real browser-like headers
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Referer": "https://www.facebook.com/",
            "Origin": "https://www.facebook.com",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }

    def log_info(self, message):
        """Log info messages with both print and logger"""
        print(f"[*] {message}")
        logger.info(message)

    def log_success(self, message):
        """Log success messages with both print and logger"""
        print(f"[+] {message}")
        logger.info(f"SUCCESS: {message}")

    def log_error(self, message):
        """Log error messages with both print and logger"""
        print(f"[-] {message}")
        logger.error(message)

    def log_debug(self, message):
        """Log debug messages if debug mode is enabled"""
        print(f"[DEBUG] {message}")
        logger.debug(message)

    def random_delay(self, min_sec=0.5, max_sec=2.0):
        """Add a natural delay to simulate human interaction"""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
        return delay

    def extract_form_data(self, html_content):
        """Extract form inputs from login page HTML"""
        form_data = {}

        # Find all input fields
        input_pattern = (
            r'<input[^>]*name=["\'](.*?)["\'][^>]*(?:value=["\'](.*?)["\'])?'
        )
        inputs = re.findall(input_pattern, html_content)

        for name, value in inputs:
            form_data[name] = value

        # Look for the special Facebook tokens
        fb_dtsg_pattern = r'"(?:dtsg|fb_dtsg)":\s*{?"token"?:?\s*"([^"]*)"'
        jazoest_pattern = r'"jazoest":(?:"([^"]*)"|\s*(\d+))'
        lsd_pattern = r'"lsd":(?:"([^"]*)"|\s*"([^"]*)")'

        # Extract fb_dtsg
        fb_dtsg_match = re.search(fb_dtsg_pattern, html_content)
        if fb_dtsg_match:
            form_data["fb_dtsg"] = fb_dtsg_match.group(1)

        # Extract jazoest
        jazoest_match = re.search(jazoest_pattern, html_content)
        if jazoest_match:
            form_data["jazoest"] = jazoest_match.group(1) or jazoest_match.group(2)

        # Extract lsd
        lsd_match = re.search(lsd_pattern, html_content)
        if lsd_match:
            form_data["lsd"] = lsd_match.group(1) or lsd_match.group(2)

        return form_data

    def find_action_url(self, html_content):
        """Find the form action URL"""
        # Look for form with id="login_form" or similar
        form_pattern = r'<form[^>]*(?:id=["\'](login[_-]form|loginform)["\'])?[^>]*action=["\'](.*?)["\']'
        form_match = re.search(form_pattern, html_content)

        if form_match:
            return form_match.group(2)

        # Fallback to looking for any form with login in the action URL
        alt_form_pattern = r'<form[^>]*action=["\'](.*?login.*?)["\']'
        alt_form_match = re.search(alt_form_pattern, html_content)

        if alt_form_match:
            return alt_form_match.group(1)

        # Default fallback
        return "https://www.facebook.com/login/device-based/regular/login/"

    def check_login_success(self, response):
        """Check if login was successful based on response"""
        # Check for successful login indicators
        if "c_user" in self.session.cookies:
            return True

        # Check if we were redirected to a non-login page
        if "login" not in response.url and "checkpoint" not in response.url:
            # Check for presence of common elements in logged-in pages
            logged_in_indicators = [
                'id="mount_0_0_"',
                '<div class="x9f619 x1n2onr6',  # Modern FB UI container
                'id="ssrb_root_content"',
                'id="facebook"',
                'id="globalContainer"',
            ]

            for indicator in logged_in_indicators:
                if indicator in response.text:
                    return True

        return False

    def direct_login(self):
        """
        Perform a direct login to Facebook that mimics browser behavior closely
        """
        try:
            self.log_info("Starting simplified direct login method")

            # Visit the homepage first to get initial cookies
            self.log_info("Visiting Facebook homepage")
            initial_response = self.session.get(
                "https://www.facebook.com/", headers=self.headers, timeout=self.timeout
            )

            if not initial_response.ok:
                self.log_error(
                    f"Failed to load homepage: {initial_response.status_code}"
                )
                return None, None

            self.random_delay(0.8, 1.5)

            # Now go to the login page
            self.log_info("Loading login page")
            login_response = self.session.get(
                "https://www.facebook.com/login",
                headers=self.headers,
                timeout=self.timeout,
            )

            if not login_response.ok:
                self.log_error(
                    f"Failed to load login page: {login_response.status_code}"
                )
                return None, None

            # Extract form data
            form_data = self.extract_form_data(login_response.text)
            self.log_debug(f"Extracted form fields: {', '.join(form_data.keys())}")

            # Find the form action URL
            action_url = self.find_action_url(login_response.text)
            self.log_debug(f"Form action URL: {action_url}")

            # If action_url is relative, make it absolute
            if action_url.startswith("/"):
                action_url = f"https://www.facebook.com{action_url}"
            elif not action_url.startswith("http"):
                action_url = f"https://www.facebook.com/{action_url}"

            # Add credentials to the form data
            form_data["email"] = self.email
            form_data["pass"] = self.password

            # Common form fields if they were not found
            if "login" not in form_data:
                form_data["login"] = "1"

            if "lsd" not in form_data:
                # Generate a fallback LSD token if not found
                form_data["lsd"] = "".join(
                    random.choices(
                        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
                        k=10,
                    )
                )

            # Simulate typing delay
            self.log_info("Entering credentials")
            self.random_delay(1.0, 2.0)

            # Update headers for the POST request
            post_headers = self.headers.copy()
            post_headers["Content-Type"] = "application/x-www-form-urlencoded"
            post_headers["Referer"] = login_response.url

            # Submit the login form
            self.log_info(f"Submitting login form to: {action_url}")
            submit_response = self.session.post(
                action_url,
                headers=post_headers,
                data=form_data,
                allow_redirects=True,
                timeout=self.timeout,
            )

            # Check login success
            if self.check_login_success(submit_response):
                self.log_success("Login successful!")
                return self.session, self.session.cookies

            # Debug login failure
            self.log_error("Login failed")
            self.log_debug(f"Response URL: {submit_response.url}")
            self.log_debug(f"Status Code: {submit_response.status_code}")
            self.log_debug(f"Cookies: {list(self.session.cookies.keys())}")

            # Check for rate limiting or security checks
            security_indicators = [
                "checkpoint",
                "Checkpoint",
                "security",
                "identify",
                "verification",
                "suspicious",
                "unusual activity",
                "We'll get back to you shortly",
                "Please try again later",
            ]

            for indicator in security_indicators:
                if indicator in submit_response.text:
                    self.log_error(f"Security check detected: {indicator}")
                    break

            return None, None

        except Exception as e:
            self.log_error(f"Error during direct login: {str(e)}")
            return None, None


def try_cloud_login(email, password):
    """
    Attempt login with the cloud-optimized method

    Returns:
        tuple: (session object, cookies) or (None, None) if failed
    """
    login_handler = CloudLogin(email, password)
    return login_handler.direct_login()
