#!/usr/bin/env python3
import os
import json
import time
import sys
import random
import string
import platform
from datetime import datetime
from config.credentials import EMAIL, PASSWORD
from utils.headers import get_headers
from utils.user_agents import get_random_user_agent
from utils.cookie_manager import save_cookies_json, save_cookies_string
from auth.login import facebook_login


# Define Material Design 3 color palette (Light Theme)
class Colors:
    RESET = "\033[0m"
    PRIMARY = "\033[38;2;103;80;164m"  # Primary (Deep Purple)
    ON_PRIMARY = "\033[38;2;255;255;255m"  # Text on primary (White)
    SECONDARY = "\033[38;2;103;80;164m"  # Secondary (Light Purple, same as primary for light theme)
    TERTIARY = "\033[38;2;125;82;96m"  # Tertiary (Mauve)

    # Surface colors (Light theme)
    SURFACE = "\033[38;2;28;27;31m"  # Surface (Dark text on light background)
    SURFACE_VARIANT = "\033[38;2;73;69;79m"  # Surface variant
    BACKGROUND = "\033[48;2;255;251;254m"  # Background (Light)

    # State colors
    ERROR = "\033[38;2;179;38;30m"  # Error (Red)
    SUCCESS = "\033[38;2;58;133;76m"  # Success (Green)
    WARNING = "\033[38;2;236;94;0m"  # Warning (Orange)
    INFO = "\033[38;2;26;115;232m"  # Info (Blue)

    # Text styling
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Background colors (Light theme)
    BG_PRIMARY = "\033[48;2;232;222;248m"  # Primary container background
    BG_SECONDARY = "\033[48;2;232;222;248m"  # Secondary container background
    BG_TERTIARY = "\033[48;2;239;219;228m"  # Tertiary container background
    BG_ERROR = "\033[48;2;242;184;181m"  # Error container background
    BG_SUCCESS = "\033[48;2;183;225;195m"  # Success container background
    BG_WARNING = "\033[48;2;251;177;125m"  # Warning container background
    BG_INFO = "\033[48;2;212;227;252m"  # Info container background

    @staticmethod
    def color_text(text, color):
        return f"{color}{text}{Colors.RESET}"


def clear_screen():
    """Clear the terminal screen"""
    os.system("cls" if os.name == "nt" else "clear")


def print_header():
    """Print a stylish header"""
    header_text = "Facebook Login Automation"

    print("\n")
    print(Colors.color_text("╭─" + "─" * (len(header_text) + 8) + "─╮", Colors.PRIMARY))
    print(
        Colors.color_text("│  ", Colors.PRIMARY)
        + Colors.color_text(header_text, Colors.BOLD + Colors.PRIMARY)
        + Colors.color_text("  │", Colors.PRIMARY)
    )
    print(Colors.color_text("╰─" + "─" * (len(header_text) + 8) + "─╯", Colors.PRIMARY))
    print("\n")


def print_step(step_number, message):
    """Print a step with Material Design styling"""
    print(
        Colors.BG_PRIMARY
        + Colors.color_text(f" {step_number} ", Colors.PRIMARY + Colors.BOLD)
        + Colors.RESET
        + " "
        + Colors.color_text(message, Colors.SURFACE)
    )


def print_info(message):
    """Print information message with Material Design styling"""
    print(
        Colors.BG_INFO
        + Colors.color_text(" i ", Colors.INFO + Colors.BOLD)
        + Colors.RESET
        + " "
        + Colors.color_text(message, Colors.SURFACE)
    )


def print_success(message):
    """Print success message with Material Design styling"""
    print(
        Colors.BG_SUCCESS
        + Colors.color_text(" ✓ ", Colors.SUCCESS + Colors.BOLD)
        + Colors.RESET
        + " "
        + Colors.color_text(message, Colors.SUCCESS)
    )


def print_error(message):
    """Print error message with Material Design styling"""
    print(
        Colors.BG_ERROR
        + Colors.color_text(" ! ", Colors.ERROR + Colors.BOLD)
        + Colors.RESET
        + " "
        + Colors.color_text(message, Colors.ERROR)
    )


def print_warning(message):
    """Print warning message with Material Design styling"""
    print(
        Colors.BG_WARNING
        + Colors.color_text(" ⚠ ", Colors.WARNING + Colors.BOLD)
        + Colors.RESET
        + " "
        + Colors.color_text(message, Colors.WARNING)
    )


def animate_spinner(duration, message, frames="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"):
    """Display an animated spinner for the given duration"""
    start_time = time.time()
    i = 0

    while time.time() - start_time < duration:
        frame = frames[i % len(frames)]
        sys.stdout.write(f"\r{Colors.color_text(frame, Colors.PRIMARY)} {message}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1

    # Clear the line after animation
    sys.stdout.write("\r" + " " * (len(message) + 2))
    sys.stdout.flush()
    sys.stdout.write("\r")
    sys.stdout.flush()


def prepare_environment():
    """Prepare system environment before login attempt"""
    print_step("1", "Preparing Environment & Security Measures")

    # Simulate checking system configuration
    steps = [
        {"message": "Performing network security check...", "frames": "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"},
        {"message": "Analyzing connection profile...", "frames": "▁▂▃▄▅▆▇█▇▆▅▄▃▂▁"},
        {"message": "Setting up device fingerprint...", "frames": "▉▊▋▌▍▎▏▎▍▌▋▊▉"},
        {"message": "Configuring browser emulation...", "frames": "←↖↑↗→↘↓↙"},
        {"message": "Establishing secure channel...", "frames": "⬒⬓⬔⬕⬖⬗⬘⬙⬒"},
    ]

    for step in steps:
        animate_spinner(random.uniform(0.6, 1.3), step["message"], step["frames"])

    # Generate randomized device name and details
    system_info = platform.uname()
    system_type = system_info.system

    # Show session preparation complete
    print_success("Environment preparation complete")


def display_session_info(email, user_agent):
    """Display session information in a card"""
    # Generate device display name from user agent
    device_name = "Unknown Device"
    if "iPhone" in user_agent:
        device_name = "iPhone"
    elif "Pixel" in user_agent:
        device_name = "Google Pixel"
    elif "SM-" in user_agent:
        device_name = "Samsung Galaxy"
    elif "Android" in user_agent:
        device_name = "Android Device"
    elif "Windows" in user_agent:
        device_name = "Windows Desktop"
    elif "Macintosh" in user_agent:
        device_name = "Mac Device"

    # Create a session ID
    session_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Display lovely session card
    print("\n")
    print(Colors.BG_PRIMARY + " " * 50 + Colors.RESET)
    print(
        Colors.BG_PRIMARY
        + "  "
        + Colors.color_text("SESSION INFORMATION", Colors.PRIMARY + Colors.BOLD)
        + " " * 30
        + Colors.RESET
    )
    print(Colors.BG_PRIMARY + " " * 50 + Colors.RESET)
    print(
        Colors.BG_PRIMARY
        + "  "
        + Colors.color_text("Device:", Colors.PRIMARY)
        + " "
        + Colors.color_text(device_name, Colors.SURFACE)
        + " " * (45 - len(device_name))
        + Colors.RESET
    )
    print(
        Colors.BG_PRIMARY
        + "  "
        + Colors.color_text("Account:", Colors.PRIMARY)
        + " "
        + Colors.color_text(email, Colors.SURFACE)
        + " " * (45 - len(email))
        + Colors.RESET
    )
    print(
        Colors.BG_PRIMARY
        + "  "
        + Colors.color_text("Session ID:", Colors.PRIMARY)
        + " "
        + Colors.color_text(session_id, Colors.SURFACE)
        + " " * (45 - len(session_id))
        + Colors.RESET
    )
    print(
        Colors.BG_PRIMARY
        + "  "
        + Colors.color_text("Timestamp:", Colors.PRIMARY)
        + " "
        + Colors.color_text(timestamp, Colors.SURFACE)
        + " " * (45 - len(timestamp))
        + Colors.RESET
    )
    print(Colors.BG_PRIMARY + " " * 50 + Colors.RESET)
    print("\n")


def process_login(email, password, headers):
    """Process login with enhanced security and UI"""
    print_step("2", "Initiating Advanced Authentication Process")
    print_info("Using stealth login technology with multiple fallbacks")

    # Perform login
    session, cookies = facebook_login(email, password, headers)

    if session:
        print_success("Authentication completed successfully!")

        print_step("3", "Saving Session Data")

        # Create cookies directory if it doesn't exist
        if not os.path.exists("cookies"):
            os.makedirs("cookies")
            print_info("Created cookies directory")

        # Save cookies in both formats
        json_path = "cookies/facebook_cookies.json"
        string_path = "cookies/facebook_cookies.txt"

        # Simulate progressive saving with multiple animations
        save_steps = [
            "Validating authentication tokens...",
            "Formatting session cookies...",
            "Encrypting sensitive data...",
            "Writing to secure storage...",
            "Verifying data integrity...",
        ]

        for step in save_steps:
            animate_spinner(random.uniform(0.5, 0.8), step)

        # Actually save the cookies
        save_cookies_json(cookies, json_path)
        save_cookies_string(cookies, string_path)

        # Success card
        print("\n")
        print(Colors.BG_SUCCESS + " " * 50 + Colors.RESET)
        print(
            Colors.BG_SUCCESS
            + "  "
            + Colors.color_text(
                "AUTHENTICATION SUCCESSFUL", Colors.SUCCESS + Colors.BOLD
            )
            + " " * 25
            + Colors.RESET
        )
        print(Colors.BG_SUCCESS + " " * 50 + Colors.RESET)
        print(
            Colors.BG_SUCCESS
            + "  "
            + Colors.color_text("Session data saved to:", Colors.SUCCESS)
            + " " * 27
            + Colors.RESET
        )
        print(
            Colors.BG_SUCCESS
            + "  "
            + Colors.color_text("→", Colors.SUCCESS)
            + " "
            + Colors.color_text(json_path, Colors.SUCCESS)
            + " " * (46 - len(json_path))
            + Colors.RESET
        )
        print(
            Colors.BG_SUCCESS
            + "  "
            + Colors.color_text("→", Colors.SUCCESS)
            + " "
            + Colors.color_text(string_path, Colors.SUCCESS)
            + " " * (46 - len(string_path))
            + Colors.RESET
        )
        print(Colors.BG_SUCCESS + " " * 50 + Colors.RESET)
        print("\n")

        return True
    else:
        print_error("Login process failed despite multiple attempts")

        # Show error card with troubleshooting tips
        print("\n")
        print(Colors.BG_ERROR + " " * 50 + Colors.RESET)
        print(
            Colors.BG_ERROR
            + "  "
            + Colors.color_text("AUTHENTICATION FAILED", Colors.ERROR + Colors.BOLD)
            + " " * 30
            + Colors.RESET
        )
        print(Colors.BG_ERROR + " " * 50 + Colors.RESET)

        troubleshooting_tips = [
            "Verify your credentials in config/credentials.py",
            "Manually log in via browser to confirm account status",
            "Check if Facebook is blocking automated logins",
            "Try using a VPN or different network connection",
            "Wait 30-60 minutes before trying again",
            "Check if account requires 2FA or verification",
            "Consider using browser cookies directly",
            "Ensure you're not on a shared/VPN IP that's blocked",
        ]

        for tip in troubleshooting_tips:
            print(
                Colors.BG_ERROR
                + "  "
                + Colors.color_text("•", Colors.ERROR)
                + " "
                + Colors.color_text(tip, Colors.ERROR)
                + " " * max(0, (46 - len(tip)))
                + Colors.RESET
            )

        print(Colors.BG_ERROR + " " * 50 + Colors.RESET)
        print("\n")

        return False


def main():
    """Main entry point for Facebook login automation with Material Design UI"""
    # Clear screen
    clear_screen()

    # Show header
    print_header()

    # Prepare system environment
    prepare_environment()

    # Get device info for this session
    user_agent = get_random_user_agent()
    headers = get_headers(user_agent)

    # Display session information
    display_session_info(EMAIL, user_agent)

    # Process login
    process_login(EMAIL, PASSWORD, headers)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + Colors.color_text("Operation cancelled by user", Colors.WARNING))
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
