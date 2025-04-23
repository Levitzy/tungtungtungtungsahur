#!/usr/bin/env python3
import json
import time
from datetime import datetime


def format_cookies_json(cookies):
    """
    Format cookies into the JSON structure requested by user

    Args:
        cookies (list): List of cookies from requests session

    Returns:
        list: List of formatted cookie dictionaries
    """
    formatted_cookies = []
    current_time = datetime.utcnow().isoformat() + "Z"

    for cookie in cookies:
        cookie_dict = {
            "key": cookie.name,
            "value": cookie.value,
            "domain": "facebook.com",  # Normalize to main domain
            "path": cookie.path,
            "hostOnly": False,
            "creation": current_time,
            "lastAccessed": current_time,
        }
        formatted_cookies.append(cookie_dict)

    return formatted_cookies


def save_cookies_json(cookies, file_path):
    """
    Save cookies to JSON file in the requested format

    Args:
        cookies (list): List of cookies from requests session
        file_path (str): Path to save the JSON file
    """
    formatted_cookies = format_cookies_json(cookies)

    with open(file_path, "w") as f:
        json.dump(formatted_cookies, f, indent=2)


def save_cookies_string(cookies, file_path):
    """
    Save cookies as a string in the 'Cookie Appstate (String)' format

    Args:
        cookies (list): List of cookies from requests session
        file_path (str): Path to save the cookie string
    """
    cookie_string = "; ".join([f"{cookie.name}={cookie.value}" for cookie in cookies])

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
