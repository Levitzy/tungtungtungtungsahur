#!/usr/bin/env python3
import random
import time
import uuid
import platform
import string
import hashlib
import re  # Added missing import for regular expressions
from datetime import datetime


def get_timezone_offset():
    """Get the timezone offset in minutes"""
    # Get UTC offset in seconds, convert to minutes
    offset = -time.timezone // 60
    if time.localtime().tm_isdst:
        offset += 60
    return offset


def generate_device_id():
    """Generate a Facebook-style device ID"""
    # Facebook often uses formats like this for device IDs
    device_formats = [
        "android-" + "".join(random.choices(string.hexdigits.lower(), k=16)),
        "".join(random.choices(string.hexdigits.lower(), k=8))
        + "-"
        + "".join(random.choices(string.hexdigits.lower(), k=4))
        + "-"
        + "".join(random.choices(string.hexdigits.lower(), k=4))
        + "-"
        + "".join(random.choices(string.hexdigits.lower(), k=4))
        + "-"
        + "".join(random.choices(string.hexdigits.lower(), k=12)),
        "".join(random.choices(string.ascii_lowercase + string.digits, k=24)),
    ]
    return random.choice(device_formats)


def get_headers(user_agent):
    """
    Generate sophisticated browser-like headers to avoid detection

    Args:
        user_agent (str): User agent string to use

    Returns:
        dict: Dictionary of HTTP headers
    """
    # Generate a unique client ID
    client_id = generate_device_id()

    # Common screen resolutions for modern devices
    resolutions = [
        "393x873",  # Pixel 7
        "390x844",  # iPhone 13 Pro
        "412x915",  # Pixel 6 Pro
        "414x896",  # iPhone 11 Pro Max
        "360x780",  # Samsung Galaxy S21
        "375x812",  # iPhone X/XS/11 Pro
        "428x926",  # iPhone 13 Pro Max
        "360x800",  # Galaxy A series
        "412x883",  # Pixel 5
        "414x736",  # iPhone 8 Plus
        "1920x1080",  # Desktop
        "2560x1440",  # Desktop high-res
        "1366x768",  # Laptop common
        "1440x900",  # Laptop/Desktop
    ]

    # Select appropriate resolution based on device type in user agent
    if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
        # Mobile resolutions only
        resolution = random.choice(resolutions[:10])
    else:
        # Desktop resolutions
        resolution = random.choice(resolutions[10:])

    width, height = resolution.split("x")

    # Pixel density varies by device type
    if "iPhone" in user_agent:
        pixel_ratios = [2.0, 3.0]  # iPhones typically use 2x or 3x
    elif "Android" in user_agent or "Mobile" in user_agent:
        pixel_ratios = [2.0, 2.5, 2.75, 3.0, 3.5]  # Android varies more
    else:
        pixel_ratios = [1.0, 1.25, 1.5, 2.0]  # Desktop varies

    pixel_ratio = random.choice(pixel_ratios)

    # Generate a color depth that makes sense for the device
    color_depths = [24, 30, 32, 48]
    color_depth = random.choice(color_depths)

    # Connection types based on device
    if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
        connection_types = ["WIFI", "5G", "4G", "LTE", "3G"]
        connection_qualities = ["EXCELLENT", "GOOD", "MODERATE"]
    else:
        connection_types = ["WIFI", "ETHERNET"]
        connection_qualities = ["EXCELLENT", "GOOD"]

    connection_type = random.choice(connection_types)

    # Connection quality more likely to be excellent on faster connections
    # Fixed weights to match the number of items in connection_qualities
    if connection_type in ["WIFI", "5G", "ETHERNET"]:
        if len(connection_qualities) == 3:
            # For mobile devices with 3 quality levels
            connection_quality = random.choices(
                connection_qualities, weights=[70, 25, 5], k=1
            )[0]
        else:
            # For desktop with 2 quality levels
            connection_quality = random.choices(
                connection_qualities, weights=[80, 20], k=1
            )[0]
    else:
        if len(connection_qualities) == 3:
            # For mobile devices with 3 quality levels
            connection_quality = random.choices(
                connection_qualities, weights=[30, 50, 20], k=1
            )[0]
        else:
            # For desktop with 2 quality levels
            connection_quality = random.choices(
                connection_qualities, weights=[40, 60], k=1
            )[0]

    # Realistic bandwidth values based on connection type
    if connection_type == "WIFI":
        bandwidth = random.randint(15000000, 100000000)
    elif connection_type == "ETHERNET":
        bandwidth = random.randint(50000000, 150000000)
    elif connection_type == "5G":
        bandwidth = random.randint(10000000, 50000000)
    elif connection_type in ["4G", "LTE"]:
        bandwidth = random.randint(5000000, 15000000)
    else:  # 3G and others
        bandwidth = random.randint(1000000, 5000000)

    # Generate an appropriate accept language header
    languages = [
        "en-US,en;q=0.9",
        "en-US,en;q=0.8",
        "en-GB,en;q=0.9,en-US;q=0.8",
        "en-CA,en;q=0.9,en-US;q=0.8",
        "en-AU,en;q=0.9,en-US;q=0.8",
    ]
    accept_language = random.choice(languages)

    # Generate a more realistic accept header based on browser type
    if "Chrome" in user_agent:
        accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    elif "Firefox" in user_agent:
        accept = "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    elif "Safari" in user_agent and "Chrome" not in user_agent:
        accept = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    else:
        accept = (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        )

    # Platform-specific headers
    platform_name = ""
    if "Windows" in user_agent:
        platform_name = "Windows"
    elif "Macintosh" in user_agent:
        platform_name = "macOS"
    elif "iPhone" in user_agent or "iPad" in user_agent:
        platform_name = "iOS"
    elif "Android" in user_agent:
        platform_name = "Android"
    elif "Linux" in user_agent:
        platform_name = "Linux"

    # Basic headers common to all browsers
    headers = {
        "User-Agent": user_agent,
        "Accept": accept,
        "Accept-Language": accept_language,
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1" if random.random() > 0.3 else "0",  # 70% chance of DNT
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Sec-CH-UA-Platform": f'"{platform_name}"',
        "Sec-CH-UA-Platform-Version": f'"{random.randint(10, 15)}"',
        "Cache-Control": random.choice(
            ["max-age=0", "no-cache", "no-store, max-age=0"]
        ),
    }

    # If it's Chrome, add Chrome-specific headers
    if "Chrome" in user_agent:
        chrome_version = re.search(r"Chrome/(\d+)", user_agent)
        if chrome_version:
            version = chrome_version.group(1)
            headers["Sec-CH-UA"] = (
                f'"Google Chrome";v="{version}", "Chromium";v="{version}"'
            )

    # If it's Firefox, add Firefox-specific headers
    elif "Firefox" in user_agent:
        headers["TE"] = "trailers"

    # If it's Safari, add Safari-specific headers
    elif "Safari" in user_agent and "Chrome" not in user_agent:
        headers["Accept-Encoding"] = "gzip, deflate"

    # Add mobile-specific headers
    if "Mobile" in user_agent or "Android" in user_agent or "iPhone" in user_agent:
        # Mobile-specific viewport headers
        headers.update(
            {
                "Viewport-Width": width,
                "Width": width,
            }
        )

        # Facebook mobile-specific headers
        fb_headers = {
            "X-FB-HTTP-Engine": random.choice(["Liger", "WebView"]),
            "X-ASBD-ID": str(random.randint(100000, 999999)),
            "X-FB-Connection-Type": connection_type,
            "X-FB-Connection-Quality": connection_quality,
            "X-FB-Device-Group": str(random.randint(1000, 9999)),
            "X-FB-Client-IP": "True" if random.random() > 0.5 else "False",
            "X-FB-Server-Cluster": random.choice(
                ["ash", "frc", "atl", "sea", "lax", "dfw", "bos"]
            ),
            "X-FB-SIM-Operator": random.choice(
                ["310260", "310410", "310012", "311480", "310150", "310030"]
            ),
            "X-FB-Net-HNI": str(random.randint(1000, 9999)),
            "X-FB-Connection-Bandwidth": str(bandwidth),
            "X-FB-Connection-Token": hashlib.md5(
                str(datetime.now()).encode()
            ).hexdigest()[:16],
            "X-FB-Friendly-Name": random.choice(
                [
                    "FBAndroidAuthHandler",
                    "Authentication.Login",
                    "graphservice",
                    "loginsdk",
                    "m_login",
                    "auth.login",
                ]
            ),
        }

        # Add these headers with a slight randomization (not all headers all the time)
        for header, value in fb_headers.items():
            if random.random() > 0.1:  # 90% chance to include each header
                headers[header] = value

        # Add device information and timezone for more authenticity
        headers["X-FB-Timezone"] = str(get_timezone_offset())

        # Device ID that looks legitimate for Facebook
        headers["X-FB-Device-ID"] = client_id

    return headers
