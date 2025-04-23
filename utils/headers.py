#!/usr/bin/env python3
import random
import time


def get_headers(user_agent):
    """
    Generate browser-like headers to avoid detection

    Args:
        user_agent (str): User agent string to use

    Returns:
        dict: Dictionary of HTTP headers
    """
    # Common screen resolutions for mobile devices
    resolutions = [
        "412x915",
        "414x896",
        "390x844",
        "360x780",
        "375x812",
        "428x926",
        "393x851",
        "360x800",
        "412x883",
        "390x844",
    ]

    # Randomize screen resolution
    resolution = random.choice(resolutions)
    width, height = resolution.split("x")

    # Create pixel ratio - common values for mobile devices
    pixel_ratios = [2.0, 2.5, 2.75, 3.0, 3.5, 4.0]
    pixel_ratio = random.choice(pixel_ratios)

    # Base headers used by most browsers
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "TE": "trailers",
        "Viewport-Width": width,
        "X-FB-HTTP-Engine": "Liger",
        "X-ASBD-ID": "129477",
        "X-FB-Connection-Type": random.choice(["WIFI", "LTE", "4G", "5G"]),
        "X-FB-Connection-Quality": random.choice(["EXCELLENT", "GOOD"]),
        "X-FB-Client-IP": "True",
        "X-FB-Server-Cluster": random.choice(["ash", "frc", "atl", "sea", "lax"]),
        "X-FB-Device-Group": str(random.randint(1000, 9999)),
        "X-FB-SIM-Operator": random.choice(["310260", "310410", "310012", "311480"]),
        "X-FB-Net-HNI": str(random.randint(1000, 9999)),
        "X-FB-Connection-Bandwidth": str(random.randint(10000000, 30000000)),
        "X-FB-Connection-Token": "".join(
            random.choice("0123456789abcdef") for _ in range(16)
        ),
        "X-FB-Friendly-Name": "FBAndroidAuthHandler",
        "X-FB-Request-Analytics-Tags": "graphservice",
        "Priority": "u=3, i",
    }

    return headers
