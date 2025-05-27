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
import logging
import traceback

# Import specialized login modules
from auth.mobile import MobileLogin
from auth.desktop import DesktopLogin
from auth.api import ApiLogin

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("auth")


class FacebookLogin:
    def __init__(self, email, password, headers):
        """Initialize the Facebook login handler with credentials"""
        self.email = email
        self.password = password
        self.headers = headers
        self.session = requests.Session()
        self.user_agent = headers.get("User-Agent", "")
        self.cookies = None
        self.debug_mode = True
        self.rate_limited = False

        # Initialize specialized login handlers
        self.mobile_login = MobileLogin(email, password, headers)
        self.desktop_login = DesktopLogin(email, password, headers)
        self.api_login = ApiLogin(email, password, headers)

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

    def execute(self):
        """Execute the login process with multiple fallback methods"""
        # Try the API methods first as they're more reliable in cloud environments
        try:
            # First try the improved API-based login (most reliable in cloud)
            self.info("Trying improved API-based login method")
            session, cookies = self.api_login.api_based_login()
            if session and cookies:
                self.success("Successfully logged in using API-based login")
                return session, cookies

            # Short delay between attempts
            self.delay(1.0, 2.0)

            # Try mobile API login next
            self.info("Trying mobile API login method")
            session, cookies = self.api_login.mobile_api_login()
            if session and cookies:
                self.success("Successfully logged in using mobile API login")
                return session, cookies

            # If API methods fail, determine device type from user agent
            is_mobile = (
                "Mobile" in self.user_agent
                or "Android" in self.user_agent
                or "iPhone" in self.user_agent
            )

            # Different login strategies based on device type
            if is_mobile:
                self.info("Detected mobile user agent, trying mobile methods")
                methods = [
                    (self.mobile_login.stealth_mobile_login, "Stealth Mobile Login"),
                    (self.mobile_login.mobile_direct_login, "Direct Mobile Login"),
                    (
                        self.desktop_login.alternative_desktop_login,
                        "Alternative Desktop Login",
                    ),
                    (
                        self.desktop_login.standard_desktop_login,
                        "Standard Desktop Login",
                    ),
                ]
            else:
                self.info("Detected desktop user agent, trying desktop methods")
                methods = [
                    (
                        self.desktop_login.alternative_desktop_login,
                        "Alternative Desktop Login",
                    ),
                    (
                        self.desktop_login.standard_desktop_login,
                        "Standard Desktop Login",
                    ),
                    (self.mobile_login.stealth_mobile_login, "Stealth Mobile Login"),
                    (self.mobile_login.mobile_direct_login, "Direct Mobile Login"),
                ]

            # Try fallback methods
            for method_func, method_name in methods:
                try:
                    self.info(f"Attempting login via {method_name}")
                    session, cookies = method_func()

                    if session and cookies:
                        self.success(f"Successfully logged in using {method_name}")
                        return session, cookies

                    # If we got rate limited, wait longer before trying the next method
                    if (
                        hasattr(method_func.__self__, "rate_limited")
                        and method_func.__self__.rate_limited
                    ):
                        self.info(
                            "Detected rate limiting, waiting before next attempt..."
                        )
                        self.delay(5.0, 8.0)
                        method_func.__self__.rate_limited = False
                    else:
                        self.delay(2.0, 3.0)

                except Exception as e:
                    self.error(f"Error in {method_name}: {str(e)}")
                    self.debug(f"Exception details: {traceback.format_exc()}")
                    self.delay(1.0, 2.0)

            self.error("All login methods failed")
            return None, None

        except Exception as e:
            self.error(f"Unexpected error during login: {str(e)}")
            self.debug(traceback.format_exc())
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
    try:
        # Initialize the login handler
        login_handler = FacebookLogin(email, password, headers)

        # Execute login process
        return login_handler.execute()
    except Exception as e:
        logger.error(f"Unexpected error in facebook_login: {str(e)}")
        logger.error(traceback.format_exc())
        return None, None
