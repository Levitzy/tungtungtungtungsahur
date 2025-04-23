#!/usr/bin/env python3
import os
import json
from config.credentials import EMAIL, PASSWORD
from utils.headers import get_headers
from utils.user_agents import get_random_user_agent
from utils.cookie_manager import save_cookies_json, save_cookies_string
from auth.login import facebook_login


def main():
    """Main entry point for Facebook login automation"""
    print("[*] Starting Facebook Login Process...")

    # Get device info for this session
    user_agent = get_random_user_agent()
    headers = get_headers(user_agent)

    # Perform login
    session, cookies = facebook_login(EMAIL, PASSWORD, headers)

    if session:
        print("[+] Login successful!")

        # Create cookies directory if it doesn't exist
        if not os.path.exists("cookies"):
            os.makedirs("cookies")

        # Save cookies in both formats
        json_path = "cookies/facebook_cookies.json"
        string_path = "cookies/facebook_cookies.txt"

        save_cookies_json(cookies, json_path)
        save_cookies_string(cookies, string_path)

        print(f"[+] Cookies saved to {json_path} and {string_path}")
        return True
    else:
        print("[-] Login failed.")
        return False


if __name__ == "__main__":
    main()
    