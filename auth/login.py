#!/usr/bin/env python3
import re
import json
import time
import random
import requests
from bs4 import BeautifulSoup


def extract_form_data(html_content):
    """
    Extract form inputs and data from Facebook login page

    Args:
        html_content (str): HTML content of the Facebook login page

    Returns:
        dict: Dictionary of form data
    """
    soup = BeautifulSoup(html_content, "html.parser")
    form_data = {}

    # Find the login form
    login_form = soup.find("form", id="login_form") or soup.find(
        "form", action="/login/device-based/regular/login/"
    )

    if not login_form:
        # Try finding any form that seems like a login form
        login_form = soup.find("form", action=lambda x: x and "login" in x.lower())

    if login_form:
        # Extract all input fields from the form
        inputs = login_form.find_all("input")
        for input_field in inputs:
            if input_field.get("name"):
                form_data[input_field.get("name")] = input_field.get("value", "")

    # Extract FB DTSG token if available (important for Facebook authentication)
    dtsg_match = re.search(r'"dtsg":{"token":"(.*?)"', html_content)
    if dtsg_match:
        form_data["fb_dtsg"] = dtsg_match.group(1)

    # Extract lsd token (another important token for Facebook authentication)
    lsd_match = re.search(r'name="lsd" value="(.*?)"', html_content)
    if lsd_match:
        form_data["lsd"] = lsd_match.group(1)

    # Extract jazoest (another Facebook security token)
    jazoest_match = re.search(r'name="jazoest" value="(.*?)"', html_content)
    if jazoest_match:
        form_data["jazoest"] = jazoest_match.group(1)

    return form_data


def facebook_login(email, password, headers):
    """
    Log into Facebook using the mobile site (m.facebook.com)

    Args:
        email (str): Facebook email
        password (str): Facebook password
        headers (dict): HTTP headers to use for the request

    Returns:
        tuple: (requests.Session, list of cookies) if successful, (None, None) otherwise
    """
    # Create a session to maintain cookies
    session = requests.Session()

    # Add randomized delay to mimic human behavior
    time.sleep(random.uniform(1.0, 2.5))

    try:
        # First visit to get the login form and initial cookies
        print("[*] Visiting the login page...")
        initial_response = session.get(
            "https://m.facebook.com/", headers=headers, timeout=30
        )

        # Mimic human delay between requests
        time.sleep(random.uniform(0.8, 1.5))

        # Visit the login page specifically
        login_response = session.get(
            "https://m.facebook.com/login/", headers=headers, timeout=30
        )

        # Extract form data from the login page
        form_data = extract_form_data(login_response.text)

        # Add email and password to the form data
        form_data["email"] = email
        form_data["pass"] = password

        # Additional form fields that Facebook might expect
        form_data["login"] = "1"
        form_data["try_number"] = "0"
        form_data["unrecognized_tries"] = "0"
        form_data["prefill_contact_point"] = email
        form_data["prefill_source"] = "browser_dropdown"
        form_data["prefill_type"] = "password"
        form_data["first_prefill_source"] = "browser_dropdown"
        form_data["first_prefill_type"] = "password"
        form_data["had_cp_prefilled"] = "true"
        form_data["had_password_prefilled"] = "true"
        form_data["__dyn"] = ""
        form_data["__csr"] = ""
        form_data["__req"] = random.choice(["1", "2", "3", "4", "5"])
        form_data["__a"] = ""
        form_data["__user"] = "0"

        # Add slight delay to mimic typing
        time.sleep(random.uniform(1.5, 3.0))

        # Set the referer header to look more legitimate
        headers["Referer"] = "https://m.facebook.com/login/"

        print("[*] Submitting login form...")
        login_url = "https://m.facebook.com/login/device-based/regular/login/"

        # Submit the login form
        post_response = session.post(
            login_url, data=form_data, headers=headers, allow_redirects=True, timeout=30
        )

        # Check if login was successful by looking for common indicators
        if "c_user" in session.cookies:
            print("[+] Found c_user cookie - login appears successful")

            # Follow any redirects to finalize the login process
            time.sleep(random.uniform(0.5, 1.0))

            # Visit the home page to confirm login and get any final cookies
            home_response = session.get(
                "https://m.facebook.com/home.php", headers=headers, timeout=30
            )

            # Return the session and its cookies
            return session, session.cookies

        elif "checkpoint" in post_response.url:
            print("[-] Login blocked by Facebook security checkpoint")
            return None, None

        elif "login" in post_response.url or "/login/" in post_response.url:
            print("[-] Still on login page - credentials may be incorrect")
            return None, None

        else:
            # If we can't determine if login failed or succeeded, check for key indicators
            if "logout" in post_response.text or "Logout" in post_response.text:
                print("[+] Found logout reference - login appears successful")
                return session, session.cookies

            # Check for other indicators that login failed
            elif (
                "The email or mobile number you entered isn't connected"
                in post_response.text
            ):
                print("[-] Email not recognized by Facebook")
                return None, None

            elif "The password you've entered is incorrect" in post_response.text:
                print("[-] Incorrect password")
                return None, None

            else:
                print("[?] Unclear login status - checking cookies...")

                # If we have xs and c_user cookies, login was probably successful
                if "xs" in session.cookies and "c_user" in session.cookies:
                    print("[+] Found authentication cookies - login appears successful")
                    return session, session.cookies
                else:
                    print("[-] Missing authentication cookies - login probably failed")
                    return None, None

    except Exception as e:
        print(f"[-] Error during login: {e}")
        return None, None
