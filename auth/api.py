#!/usr/bin/env python3
import re
import json
import time
import random
import string
import requests
import hashlib
import base64


class ApiLogin:
    def __init__(self, email, password, headers):
        """Initialize the Facebook API login handler with credentials"""
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

    def api_based_login(self):
        """
        Improved API-based login method that mimics the mobile app
        """
        try:
            self.info("Using API-based login approach...")

            # Clean session
            self.session = requests.Session()

            # API endpoint
            api_url = "https://b-api.facebook.com/method/auth.login"

            # Generate a device ID and other metadata for authenticity
            device_id = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=16)
            )

            # Generate a random locale
            locales = ["en_US", "en_GB", "en_AU", "en_CA"]
            locale = random.choice(locales)

            # Generate metadata about the "device"
            adid = "".join(random.choices(string.hexdigits.lower(), k=16))
            family_device_id = "".join(random.choices(string.hexdigits.lower(), k=16))
            advertiser_id = "".join(random.choices(string.hexdigits.lower(), k=16))
            android_id = "".join(random.choices(string.hexdigits.lower(), k=16))

            # Create API parameters with improved structure
            api_params = {
                # Authentication parameters
                "email": self.email,
                "password": self.password,
                "credentials_type": "password",
                "generate_session_cookies": "1",
                "error_detail_type": "button_with_disabled",
                "source": "login",
                "meta_inf_fbmeta": "",
                "advertiser_id": advertiser_id,
                "currently_logged_in_userid": "0",
                # API specific parameters
                "api_key": "882a8490361da98702bf97a021ddc14d",
                "access_token": "350685531728|62f8ce9f74b12f84c123cc23437a4a32",
                "format": "json",
                "sdk_version": "2",
                "return_ssl_resources": "1",
                # Device information
                "device_id": device_id,
                "family_device_id": family_device_id,
                "device_id_old": adid,
                "android_id": android_id,
                "method": "auth.login",
                "locale": locale,
                "client_country_code": locale.split("_")[1],
                # Signature and verification
                "sig": hashlib.md5(
                    (
                        f"api_key=882a8490361da98702bf97a021ddc14d"
                        f"credentials_type=password"
                        f"email={self.email}"
                        f"format=json"
                        f"generate_session_cookies=1"
                        f"locale={locale}"
                        f"method=auth.login"
                        f"password={self.password}"
                        f"return_ssl_resources=1"
                        f"v=1.0"
                        f"350685531728|62f8ce9f74b12f84c123cc23437a4a32"
                    ).encode()
                ).hexdigest(),
            }

            # Set API headers to mimic mobile app
            api_headers = {
                "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; SM-G973F Build/RP1A.200720.012)",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "close",
                "Content-Type": "application/x-www-form-urlencoded",
                "x-fb-connection-type": "mobile.LTE",
                "x-fb-connection-quality": "EXCELLENT",
                "x-fb-connection-bandwidth": str(random.randint(20000000, 40000000)),
                "x-fb-net-hni": str(random.randint(20000, 40000)),
                "x-fb-device-group": "5120",
                "X-FB-Friendly-Name": "authenticate",
                "X-FB-Request-Analytics-Tags": "graphservice",
                "X-FB-HTTP-Engine": "Liger",
                "X-FB-Client-IP": "True",
                "X-FB-Server-Cluster": "True",
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

    def graph_api_login(self):
        """
        Alternative API login method using Graph API
        """
        try:
            self.info("Using Graph API login approach...")

            # Clean session
            self.session = requests.Session()

            # Graph API endpoint for authentication
            api_url = "https://graph.facebook.com/auth/login"

            # Generate device information
            device_id = "".join(
                random.choices(string.ascii_lowercase + string.digits, k=16)
            )
            machine_id = "".join(random.choices(string.hexdigits.lower(), k=24))
            adid = "".join(random.choices(string.hexdigits.lower(), k=16))

            # Create a CRYPT value (mimicking FB app)
            crypt = base64.b64encode(
                json.dumps(
                    {
                        "i": machine_id,
                        "t": int(time.time()),
                        "m": 0,
                        "c": "".join(
                            random.choices(string.ascii_letters + string.digits, k=22)
                        ),
                    }
                ).encode()
            ).decode()

            # Create API parameters with detailed device information
            api_params = {
                # Authentication parameters
                "email": self.email,
                "password": self.password,
                "format": "json",
                "generate_session_cookies": "1",
                "generate_analytics_claim": "1",
                "generate_machine_id": "1",
                "locale": "en_US",
                "client_country_code": "US",
                # Device information
                "device_id": device_id,
                "cpl": "true",
                "family_device_id": device_id,
                "credentials_type": "device_based_login_password",
                "adid": adid,
                "identifier": self.email,
                "machine_id": machine_id,
                "error_detail_type": "button_with_disabled",
                # Device-based sign-in parameters
                "fb_api_req_friendly_name": "authenticate",
                "fb_api_caller_class": "com.facebook.account.login.protocol.Fb4aAuthHandler",
                "access_token": "350685531728|62f8ce9f74b12f84c123cc23437a4a32",
                "crypt": crypt,
            }

            # Set API headers to mimic FB app
            graph_headers = {
                "User-Agent": "FBAndroid/431.0.0.30.118;FBMF/samsung;FBBD/samsung;FBDV/SM-G973F;FBSV/11;FBCA/arm64-v8a:null;FBDM/{density=2.25}",
                "Accept-Encoding": "gzip, deflate",
                "Connection": "close",
                "Content-Type": "application/x-www-form-urlencoded",
                "X-FB-Connection-Type": "WIFI",
                "X-FB-Net-HNI": str(random.randint(20000, 40000)),
                "X-FB-HTTP-Engine": "Liger",
                "X-FB-Client-IP": "True",
                "X-FB-Server-Cluster": "True",
                "X-FB-SIM-HNI": str(random.randint(20000, 40000)),
                "Authorization": "OAuth 350685531728|62f8ce9f74b12f84c123cc23437a4a32",
                "X-FB-Connection-Quality": "EXCELLENT",
                "X-FB-Friendly-Name": "authenticate",
                "X-FB-Request-Analytics-Tags": "graphservice",
                "X-Tigon-Is-Retry": "False",
                "X-FB-Device-Group": str(random.randint(1000, 9999)),
            }

            # Submit API request
            self.info("Sending Graph API login request...")
            self.delay(1.0, 2.0)

            api_response = self.session.post(
                api_url, data=api_params, headers=graph_headers, timeout=30
            )

            # Parse the response
            try:
                response_data = api_response.json()

                if "access_token" in response_data or "session_key" in response_data:
                    self.success("Graph API login successful!")

                    # If session cookies are available, use them
                    if "session_cookies" in response_data:
                        for cookie in response_data["session_cookies"]:
                            self.session.cookies.set(
                                cookie["name"], cookie["value"], domain=".facebook.com"
                            )

                    # Sometimes the access token can be used to get session cookies
                    elif "access_token" in response_data:
                        self.info("Got access token, retrieving session cookies...")
                        self.delay(0.5, 1.0)

                        cookie_url = "https://graph.facebook.com/v16.0/cookie_jar"
                        cookie_headers = graph_headers.copy()

                        if "access_token" in response_data:
                            cookie_headers["Authorization"] = (
                                f"Bearer {response_data['access_token']}"
                            )

                        cookie_response = self.session.get(
                            cookie_url, headers=cookie_headers, timeout=30
                        )

                        try:
                            cookie_data = cookie_response.json()
                            if "data" in cookie_data and cookie_data["data"].get(
                                "cookies"
                            ):
                                for cookie in cookie_data["data"]["cookies"]:
                                    self.session.cookies.set(
                                        cookie["name"],
                                        cookie["value"],
                                        domain=".facebook.com",
                                    )
                        except:
                            self.error("Failed to parse cookie response")

                    return self.session, self.session.cookies

                elif "error" in response_data:
                    self.error(
                        f"Graph API login error: {response_data.get('error', {}).get('message', 'Unknown error')}"
                    )

            except ValueError:
                self.error("Failed to parse Graph API response")

            return None, None

        except Exception as e:
            self.error(f"Error in graph_api_login: {str(e)}")
            return None, None
