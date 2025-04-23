#!/usr/bin/env python3
import json
import time
import random
from datetime import datetime, timedelta


def format_cookies_json(cookies):
    """
    Format cookies into the JSON structure matching Facebook cookie format

    Args:
        cookies (list): List of cookies from requests session

    Returns:
        list: List of formatted cookie dictionaries
    """
    formatted_cookies = []
    base_time = datetime.utcnow()
    # Base ISO time with Z suffix for UTC
    base_time_str = base_time.isoformat() + "Z"

    # Extract existing cookie values
    cookie_dict = {cookie.name: cookie.value for cookie in cookies}

    # Prepare common Facebook cookies
    cookie_templates = [
        # Core authentication cookies
        {"key": "datr", "domain": "facebook.com", "path": "/", "hostOnly": False},
        {"key": "c_user", "domain": "facebook.com", "path": "/", "hostOnly": False},
        {"key": "xs", "domain": "facebook.com", "path": "/", "hostOnly": False},
        {"key": "fr", "domain": "facebook.com", "path": "/", "hostOnly": False},
        # Additional cookies that may be present
        {"key": "sb", "domain": "facebook.com", "path": "/", "hostOnly": False},
        {
            "key": "m_pixel_ratio",
            "value": "2.4000000953674316",
            "domain": "facebook.com",
            "path": "/",
            "hostOnly": False,
        },
        {
            "key": "wd",
            "value": "492x880",
            "domain": "facebook.com",
            "path": "/",
            "hostOnly": False,
        },
        {
            "key": "locale",
            "value": "en_US",
            "domain": "facebook.com",
            "path": "/",
            "hostOnly": False,
        },
        {
            "key": "vpd",
            "value": "v1%3B880x492x2.4000000953674316",
            "domain": "facebook.com",
            "path": "/",
            "hostOnly": False,
        },
    ]

    # Generate cookies in the correct order
    used_cookies = set()
    for template in cookie_templates:
        key = template["key"]

        # If this cookie exists in our session cookies, use its value
        if key in cookie_dict:
            value = cookie_dict[key]
            used_cookies.add(key)
        # Otherwise use the template value if it exists
        elif "value" in template:
            value = template["value"]
        # Skip if we don't have a value
        else:
            continue

        # Create slightly different timestamps for each cookie
        time_offset = timedelta(milliseconds=random.randint(1, 10))
        creation_time = (base_time - time_offset).isoformat() + "Z"
        access_time = base_time_str

        cookie_entry = {
            "key": key,
            "value": value,
            "domain": template["domain"],
            "path": template["path"],
            "hostOnly": template["hostOnly"],
            "creation": creation_time,
            "lastAccessed": access_time,
        }

        formatted_cookies.append(cookie_entry)

    # Add any remaining cookies from the session that weren't in our templates
    for cookie in cookies:
        if cookie.name not in used_cookies:
            time_offset = timedelta(milliseconds=random.randint(1, 10))
            creation_time = (base_time - time_offset).isoformat() + "Z"

            cookie_entry = {
                "key": cookie.name,
                "value": cookie.value,
                "domain": "facebook.com",  # Normalize to main domain
                "path": cookie.path if hasattr(cookie, "path") and cookie.path else "/",
                "hostOnly": False,
                "creation": creation_time,
                "lastAccessed": base_time_str,
            }

            formatted_cookies.append(cookie_entry)

    return formatted_cookies


def format_cookies_string(cookies):
    """
    Format cookies as a string in the Facebook cookie string format

    Args:
        cookies (list): List of cookies from requests session

    Returns:
        str: Cookie string formatted for Facebook
    """
    # Extract actual cookies
    cookie_dict = {cookie.name: cookie.value for cookie in cookies}

    # Add common cookies if they don't exist
    if "m_pixel_ratio" not in cookie_dict:
        cookie_dict["m_pixel_ratio"] = "2.4000000953674316"
    if "wd" not in cookie_dict:
        cookie_dict["wd"] = "492x880"
    if "locale" not in cookie_dict:
        cookie_dict["locale"] = "en_US"
    if "vpd" not in cookie_dict:
        cookie_dict["vpd"] = "v1%3B880x492x2.4000000953674316"

    # Join all cookies in name=value format
    cookie_string = "; ".join(
        [f"{name}={value}" for name, value in cookie_dict.items()]
    )

    return cookie_string


def save_cookies_json(cookies, file_path):
    """
    Save cookies to JSON file in the Facebook JSON format

    Args:
        cookies (list): List of cookies from requests session
        file_path (str): Path to save the JSON file
    """
    formatted_cookies = format_cookies_json(cookies)

    with open(file_path, "w") as f:
        json.dump(formatted_cookies, f, indent=3)


def save_cookies_string(cookies, file_path):
    """
    Save cookies as a string in the Facebook cookie string format

    Args:
        cookies (list): List of cookies from requests session
        file_path (str): Path to save the cookie string
    """
    cookie_string = format_cookies_string(cookies)

    with open(file_path, "w") as f:
        f.write(cookie_string)


def load_cookies_json(file_path):
    """
    Load cookies from a JSON file

    Args:
        file_path (str): Path to the JSON cookie file

    Returns:
        dict: Dictionary of cookies for requests
    """
    with open(file_path, "r") as f:
        cookies_data = json.load(f)

    # Convert to format usable by requests
    cookies_dict = {}
    for cookie in cookies_data:
        cookies_dict[cookie["key"]] = cookie["value"]

    return cookies_dict
