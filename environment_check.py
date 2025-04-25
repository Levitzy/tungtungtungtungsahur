#!/usr/bin/env python3
"""
Environment checker utility for Facebook Auth System
This script checks various aspects of the environment that might affect authentication
"""

import os
import sys
import json
import socket
import platform
import requests
import logging
import traceback
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("environment_check.log")],
)

logger = logging.getLogger("env_check")


def check_internet_connectivity():
    """Check basic internet connectivity"""
    logger.info("Checking internet connectivity...")

    test_sites = [
        "https://www.google.com",
        "https://www.facebook.com",
        "https://www.amazon.com",
        "https://www.microsoft.com",
    ]

    results = {}

    for site in test_sites:
        try:
            start_time = datetime.now()
            response = requests.get(site, timeout=10)
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()

            results[site] = {
                "status_code": response.status_code,
                "accessible": response.status_code < 400,
                "response_time": elapsed,
            }
            logger.info(
                f"✓ {site}: Status {response.status_code}, Time: {elapsed:.2f}s"
            )
        except Exception as e:
            logger.error(f"✗ {site}: Error - {str(e)}")
            results[site] = {"status_code": None, "accessible": False, "error": str(e)}

    return results


def check_facebook_endpoints():
    """Check specific Facebook endpoints used by the auth system"""
    logger.info("Checking Facebook API endpoints...")

    endpoints = [
        "https://b-api.facebook.com/method/auth.login",
        "https://graph.facebook.com/auth/login",
        "https://www.facebook.com/login.php",
        "https://m.facebook.com/login.php",
        "https://mbasic.facebook.com/login.php",
    ]

    results = {}

    # Use generic headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    for endpoint in endpoints:
        try:
            start_time = datetime.now()
            # Only send HEAD request to avoid triggering security measures
            response = requests.head(endpoint, headers=headers, timeout=10)
            end_time = datetime.now()
            elapsed = (end_time - start_time).total_seconds()

            results[endpoint] = {
                "status_code": response.status_code,
                "accessible": response.status_code < 400,
                "response_time": elapsed,
            }

            status = "✓" if response.status_code < 400 else "⚠"
            logger.info(
                f"{status} {endpoint}: Status {response.status_code}, Time: {elapsed:.2f}s"
            )
        except Exception as e:
            logger.error(f"✗ {endpoint}: Error - {str(e)}")
            results[endpoint] = {
                "status_code": None,
                "accessible": False,
                "error": str(e),
            }

    return results


def check_dns_resolution():
    """Check DNS resolution for key domains"""
    logger.info("Checking DNS resolution...")

    domains = [
        "www.facebook.com",
        "b-api.facebook.com",
        "graph.facebook.com",
        "m.facebook.com",
        "mbasic.facebook.com",
    ]

    results = {}

    for domain in domains:
        try:
            ip_address = socket.gethostbyname(domain)
            results[domain] = {"resolved": True, "ip_address": ip_address}
            logger.info(f"✓ {domain} resolves to {ip_address}")
        except socket.gaierror as e:
            logger.error(f"✗ {domain}: DNS resolution failed - {str(e)}")
            results[domain] = {"resolved": False, "error": str(e)}

    return results


def check_outbound_ip():
    """Check the outbound IP address of this machine"""
    logger.info("Checking outbound IP address...")

    ip_services = [
        "https://api.ipify.org?format=json",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
    ]

    for service in ip_services:
        try:
            response = requests.get(service, timeout=5)
            if response.status_code == 200:
                if service.endswith("json"):
                    ip = response.json().get("ip", "Unknown")
                else:
                    ip = response.text.strip()

                logger.info(f"Outbound IP address: {ip} (via {service})")
                return {"ip": ip, "source": service}
        except Exception as e:
            logger.warning(f"Could not get IP from {service}: {str(e)}")

    logger.error("Failed to determine outbound IP address")
    return {"ip": "Unknown", "source": None}


def check_environment_variables():
    """Check important environment variables"""
    logger.info("Checking environment variables...")

    # List of environment variables to check
    variables = [
        "PORT",
        "DEBUG",
        "PYTHONPATH",
        "PATH",
        "HOME",
        "USER",
        "LOGNAME",
        "LANG",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "NO_PROXY",
    ]

    results = {}

    for var in variables:
        value = os.environ.get(var)
        results[var] = value
        if value is not None:
            logger.info(f"{var} = {value}")
        else:
            logger.info(f"{var} is not set")

    return results


def check_file_permissions():
    """Check permissions on important directories and files"""
    logger.info("Checking file permissions...")

    paths = [
        ".",
        "./sessions",
        "./auth",
        "./static",
        "./templates",
        "./logs",
        "./server.py",
        "./main.py",
    ]

    results = {}

    for path in paths:
        try:
            if os.path.exists(path):
                stats = os.stat(path)
                is_dir = os.path.isdir(path)

                # Create readable permission string
                mode = stats.st_mode
                perms = ""
                for who in "USR", "GRP", "OTH":
                    for what in "R", "W", "X":
                        perm = getattr(stats, f"S_I{what}{who}")
                        perms += what.lower() if mode & perm else "-"

                results[path] = {
                    "exists": True,
                    "type": "directory" if is_dir else "file",
                    "permissions": perms,
                    "mode": oct(mode)[-3:],
                    "uid": stats.st_uid,
                    "gid": stats.st_gid,
                }

                logger.info(
                    f"✓ {path}: {'dir' if is_dir else 'file'} with permissions {perms} ({oct(mode)[-3:]})"
                )
            else:
                results[path] = {"exists": False}
                logger.warning(f"✗ {path} does not exist")
        except Exception as e:
            logger.error(f"Error checking {path}: {str(e)}")
            results[path] = {"exists": "error", "error": str(e)}

    return results


def check_system_info():
    """Get basic system information"""
    logger.info("Collecting system information...")

    info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "system": platform.system(),
        "release": platform.release(),
        "processor": platform.processor(),
        "architecture": platform.architecture(),
        "hostname": socket.gethostname(),
        "time": datetime.now().isoformat(),
    }

    for key, value in info.items():
        logger.info(f"{key}: {value}")

    return info


def main():
    """Run all environment checks and save results"""
    try:
        logger.info("Starting environment check")

        results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": check_system_info(),
            "environment_variables": check_environment_variables(),
            "file_permissions": check_file_permissions(),
            "internet_connectivity": check_internet_connectivity(),
            "dns_resolution": check_dns_resolution(),
            "outbound_ip": check_outbound_ip(),
            "facebook_endpoints": check_facebook_endpoints(),
        }

        # Save results to file
        with open("environment_check_results.json", "w") as f:
            json.dump(results, f, indent=2)

        logger.info(
            "Environment check completed and saved to environment_check_results.json"
        )
        print(
            "\nEnvironment check completed. See environment_check_results.json for details."
        )

        # Return success code
        return 0

    except Exception as e:
        logger.critical(f"Environment check failed: {str(e)}")
        logger.error(traceback.format_exc())
        print(f"Environment check failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
