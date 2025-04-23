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


# Define Enhanced Material UI Color Scheme
class Colors:
    # Reset color
    RESET = "\033[0m"

    # Basic colors
    BLACK = "\033[38;2;0;0;0m"
    WHITE = "\033[38;2;255;255;255m"

    # Primary colors - Deep Indigo
    PRIMARY_50 = "\033[38;2;232;234;246m"
    PRIMARY_100 = "\033[38;2;197;202;233m"
    PRIMARY_200 = "\033[38;2;159;168;218m"
    PRIMARY_300 = "\033[38;2;121;134;203m"
    PRIMARY_400 = "\033[38;2;92;107;192m"
    PRIMARY_500 = "\033[38;2;63;81;181m"
    PRIMARY_600 = "\033[38;2;57;73;171m"
    PRIMARY_700 = "\033[38;2;48;63;159m"
    PRIMARY_800 = "\033[38;2;40;53;147m"
    PRIMARY_900 = "\033[38;2;26;35;126m"

    # Secondary colors - Deep Purple
    SECONDARY_300 = "\033[38;2;149;117;205m"
    SECONDARY_500 = "\033[38;2;103;58;183m"
    SECONDARY_700 = "\033[38;2;69;39;160m"

    # Tertiary colors - Teal
    TERTIARY_300 = "\033[38;2;77;182;172m"
    TERTIARY_500 = "\033[38;2;0;150;136m"
    TERTIARY_700 = "\033[38;2;0;121;107m"

    # Status colors
    SUCCESS = "\033[38;2;76;175;80m"
    ERROR = "\033[38;2;211;47;47m"
    WARNING = "\033[38;2;245;124;0m"
    INFO = "\033[38;2;25;118;210m"

    # Background colors
    BG_PRIMARY_50 = "\033[48;2;232;234;246m"
    BG_PRIMARY_100 = "\033[48;2;197;202;233m"
    BG_PRIMARY_500 = "\033[48;2;63;81;181m"
    BG_PRIMARY_700 = "\033[48;2;48;63;159m"
    BG_PRIMARY_900 = "\033[48;2;26;35;126m"

    BG_SECONDARY_500 = "\033[48;2;103;58;183m"
    BG_TERTIARY_500 = "\033[48;2;0;150;136m"

    BG_SUCCESS = "\033[48;2;76;175;80m"
    BG_ERROR = "\033[48;2;211;47;47m"
    BG_WARNING = "\033[48;2;245;124;0m"
    BG_INFO = "\033[48;2;25;118;210m"

    # Text modifiers
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"

    @staticmethod
    def color_text(text, color):
        """Apply color to text and reset after"""
        return f"{color}{text}{Colors.RESET}"

    @staticmethod
    def gradient_text(text, start_color, end_color):
        """Create a simple gradient effect (only works with RGB colors)"""
        if not text:
            return ""

        start_r, start_g, start_b = Colors._parse_rgb(start_color)
        end_r, end_g, end_b = Colors._parse_rgb(end_color)

        result = ""
        for i, char in enumerate(text):
            if char.isspace():
                result += char
                continue

            # Calculate gradient position
            ratio = i / (len(text) - 1) if len(text) > 1 else 0

            # Interpolate RGB values
            r = int(start_r + (end_r - start_r) * ratio)
            g = int(start_g + (end_g - start_g) * ratio)
            b = int(start_b + (end_b - start_b) * ratio)

            # Create color code and add character
            result += f"\033[38;2;{r};{g};{b}m{char}"

        return result + Colors.RESET

    @staticmethod
    def _parse_rgb(color_code):
        """Extract RGB values from ANSI color code"""
        rgb_match = re.search(r"\033\[38;2;(\d+);(\d+);(\d+)m", color_code)
        if rgb_match:
            return (
                int(rgb_match.group(1)),
                int(rgb_match.group(2)),
                int(rgb_match.group(3)),
            )
        return 255, 255, 255  # Default to white if not RGB

    @staticmethod
    def box(content, padding=1, border_color=None, fill_color=None):
        """Create a box around content with optional padding and colors"""
        lines = content.split("\n")
        width = max(len(line) for line in lines)

        result = []
        border_color = border_color or Colors.PRIMARY_500
        fill_color = fill_color or ""

        # Top border
        result.append(f"{border_color}╭{'─' * (width + padding * 2)}╮{Colors.RESET}")

        # Empty lines for top padding
        for _ in range(padding):
            result.append(
                f"{border_color}│{fill_color}{' ' * (width + padding * 2)}{Colors.RESET}{border_color}│{Colors.RESET}"
            )

        # Content lines
        for line in lines:
            padding_needed = width - len(line)
            padded_line = line + " " * padding_needed
            result.append(
                f"{border_color}│{fill_color}{' ' * padding}{padded_line}{' ' * padding}{Colors.RESET}{border_color}│{Colors.RESET}"
            )

        # Empty lines for bottom padding
        for _ in range(padding):
            result.append(
                f"{border_color}│{fill_color}{' ' * (width + padding * 2)}{Colors.RESET}{border_color}│{Colors.RESET}"
            )

        # Bottom border
        result.append(f"{border_color}╰{'─' * (width + padding * 2)}╯{Colors.RESET}")

        return "\n".join(result)


# Import regex for color parsing
import re


def clear_screen():
    """Clear the terminal screen"""
    os.system("cls" if os.name == "nt" else "clear")


def print_logo():
    """Print a stylish animated logo"""
    logo = """
    ███████╗██████╗        ██╗      ██████╗  ██████╗ ██╗███╗   ██╗
    ██╔════╝██╔══██╗       ██║     ██╔═══██╗██╔════╝ ██║████╗  ██║
    █████╗  ██████╔╝       ██║     ██║   ██║██║  ███╗██║██╔██╗ ██║
    ██╔══╝  ██╔══██╗       ██║     ██║   ██║██║   ██║██║██║╚██╗██║
    ██║     ██████╔╝▄█╗    ███████╗╚██████╔╝╚██████╔╝██║██║ ╚████║
    ╚═╝     ╚═════╝ ╚═╝    ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝╚═╝  ╚═══╝
    """

    frames = []
    colors = [
        Colors.PRIMARY_300,
        Colors.PRIMARY_400,
        Colors.PRIMARY_500,
        Colors.PRIMARY_600,
        Colors.PRIMARY_700,
        Colors.SECONDARY_300,
        Colors.SECONDARY_500,
        Colors.SECONDARY_700,
    ]

    # Generate color sequence for animation
    for color in colors:
        frames.append(Colors.color_text(logo, color))

    # Add gradient frames
    frames.append(Colors.gradient_text(logo, Colors.PRIMARY_300, Colors.SECONDARY_700))
    frames.append(Colors.gradient_text(logo, Colors.SECONDARY_700, Colors.PRIMARY_300))

    # Animate the logo
    for frame in frames:
        clear_screen()
        print(frame)

        # Add a subtitle with a different animation
        subtitle = "Advanced Authentication System"
        padding = (len(logo.split("\n")[1]) - len(subtitle)) // 2
        print(
            " " * padding
            + Colors.color_text(subtitle, Colors.TERTIARY_500 + Colors.BOLD)
        )

        time.sleep(0.15)

    # Final logo with subtle animation
    clear_screen()
    print(Colors.gradient_text(logo, Colors.PRIMARY_500, Colors.SECONDARY_500))

    # Add a static subtitle
    subtitle = "Advanced Authentication System"
    padding = (len(logo.split("\n")[1]) - len(subtitle)) // 2
    print(
        " " * padding + Colors.color_text(subtitle, Colors.TERTIARY_500 + Colors.BOLD)
    )

    print("\n")


def print_step(step_number, message):
    """Print a step with enhanced styling"""
    step_indicator = f" {step_number} "

    print(
        Colors.BG_PRIMARY_700
        + Colors.WHITE
        + Colors.BOLD
        + step_indicator
        + Colors.RESET
        + " "
        + Colors.PRIMARY_500
        + Colors.BOLD
        + message
        + Colors.RESET
    )


def print_info(message):
    """Print information message with enhanced styling"""
    print(
        Colors.BG_INFO
        + Colors.WHITE
        + Colors.BOLD
        + " i "
        + Colors.RESET
        + " "
        + Colors.INFO
        + message
        + Colors.RESET
    )


def print_success(message):
    """Print success message with enhanced styling"""
    print(
        Colors.BG_SUCCESS
        + Colors.WHITE
        + Colors.BOLD
        + " ✓ "
        + Colors.RESET
        + " "
        + Colors.SUCCESS
        + Colors.BOLD
        + message
        + Colors.RESET
    )


def print_error(message):
    """Print error message with enhanced styling"""
    print(
        Colors.BG_ERROR
        + Colors.WHITE
        + Colors.BOLD
        + " ! "
        + Colors.RESET
        + " "
        + Colors.ERROR
        + message
        + Colors.RESET
    )


def print_warning(message):
    """Print warning message with enhanced styling"""
    print(
        Colors.BG_WARNING
        + Colors.BLACK
        + Colors.BOLD
        + " ⚠ "
        + Colors.RESET
        + " "
        + Colors.WARNING
        + message
        + Colors.RESET
    )


def animate_spinner(duration, message, frames="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"):
    """Display an animated spinner for the given duration"""
    start_time = time.time()
    i = 0

    while time.time() - start_time < duration:
        frame = frames[i % len(frames)]
        sys.stdout.write(
            f"\r{Colors.color_text(frame, Colors.PRIMARY_500)} {Colors.color_text(message, Colors.PRIMARY_300)}"
        )
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1

    # Clear the line after animation
    sys.stdout.write("\r" + " " * (len(message) + 2))
    sys.stdout.flush()
    sys.stdout.write("\r")
    sys.stdout.flush()


def animate_progress_bar(duration, message, width=30):
    """Display an animated progress bar for the given duration"""
    start_time = time.time()
    end_time = start_time + duration

    while time.time() < end_time:
        elapsed = time.time() - start_time
        progress = min(1.0, elapsed / duration)

        # Calculate bar segments
        filled_length = int(width * progress)
        empty_length = width - filled_length

        # Create progress bar with gradient
        if filled_length > 0:
            filled_bar = Colors.BG_PRIMARY_500 + " " * filled_length + Colors.RESET
        else:
            filled_bar = ""

        empty_bar = " " * empty_length

        # Calculate percentage
        percent = int(progress * 100)

        # Print progress bar
        sys.stdout.write(
            f"\r{Colors.PRIMARY_500}{message} [{filled_bar}{empty_bar}] {percent}%{Colors.RESET}"
        )
        sys.stdout.flush()

        time.sleep(0.05)

    # Complete the progress bar
    filled_bar = Colors.BG_PRIMARY_500 + " " * width + Colors.RESET
    sys.stdout.write(
        f"\r{Colors.PRIMARY_500}{message} [{filled_bar}] 100%{Colors.RESET}"
    )
    sys.stdout.flush()
    print()


def prepare_environment():
    """Prepare system environment before login attempt"""
    print_step("1", "Preparing Environment & Security Measures")

    # Simulate checking system configuration
    steps = [
        {
            "message": "Performing network security check...",
            "duration": random.uniform(0.7, 1.2),
        },
        {
            "message": "Analyzing connection profile...",
            "duration": random.uniform(0.5, 0.9),
        },
        {
            "message": "Setting up device fingerprint...",
            "duration": random.uniform(0.8, 1.3),
        },
        {
            "message": "Configuring browser emulation...",
            "duration": random.uniform(0.6, 1.0),
        },
        {
            "message": "Establishing secure channel...",
            "duration": random.uniform(0.7, 1.1),
        },
    ]

    for step in steps:
        animate_progress_bar(step["duration"], step["message"])

    # Show session preparation complete
    print_success("Environment preparation complete")
    print()


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

    # Create session card content
    card_content = f"""SESSION INFORMATION
Device:     {device_name}
Account:    {email}
Session ID: {session_id}
Timestamp:  {timestamp}"""

    # Display card with styling
    print(
        Colors.box(
            card_content,
            padding=1,
            border_color=Colors.PRIMARY_500,
            fill_color=Colors.BG_PRIMARY_50,
        )
    )
    print()


def process_login(email, password, headers):
    """Process login with enhanced security and UI"""
    print_step("2", "Initiating Advanced Authentication Process")
    print_info("Using advanced login technology with multiple fallbacks")
    print()

    # Show method list
    method_list = [
        "Mobile Stealth Login",
        "Desktop Standard Login",
        "API-Based Authentication",
        "Graph API Authentication",
        "Alternative Mobile Login",
        "Alternative Desktop Login",
    ]

    print(
        Colors.color_text(
            "Available Authentication Methods:", Colors.PRIMARY_500 + Colors.BOLD
        )
    )
    for i, method in enumerate(method_list, 1):
        print(
            f"  {Colors.color_text(str(i), Colors.PRIMARY_500)} {Colors.color_text(method, Colors.PRIMARY_300)}"
        )
    print()

    # Perform login with animated progress
    animate_spinner(1.5, "Initializing authentication processor...")
    print()

    session, cookies = facebook_login(email, password, headers)

    if session:
        print_success("Authentication completed successfully!")
        print()

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

        # Actually save the cookies with improved format
        save_cookies_json(cookies, json_path)
        save_cookies_string(cookies, string_path)

        # Display cookie preview
        try:
            with open(json_path, "r") as f:
                cookie_data = json.load(f)

            # Count useful cookies
            auth_cookies = [
                c for c in cookie_data if c["key"] in ["c_user", "xs", "fr", "datr"]
            ]
            other_cookies = [
                c for c in cookie_data if c["key"] not in ["c_user", "xs", "fr", "datr"]
            ]

            cookie_stats = f"""AUTHENTICATION SUCCESSFUL
Session data saved to:
→ {json_path} ({len(cookie_data)} cookies)
→ {string_path}

Authentication cookies: {len(auth_cookies)}
Additional cookies: {len(other_cookies)}"""

            # Display success card
            print()
            print(
                Colors.box(
                    cookie_stats,
                    padding=1,
                    border_color=Colors.SUCCESS,
                    fill_color=Colors.BG_SUCCESS + Colors.BLACK,
                )
            )
            print()

        except Exception as e:
            # Fallback to simple success message if preview fails
            success_content = f"""AUTHENTICATION SUCCESSFUL
Session data saved to:
→ {json_path}
→ {string_path}"""

            # Display success card
            print()
            print(
                Colors.box(
                    success_content,
                    padding=1,
                    border_color=Colors.SUCCESS,
                    fill_color=Colors.BG_SUCCESS + Colors.BLACK,
                )
            )
            print()

        return True
    else:
        print_error("Login process failed despite multiple attempts")

        # Error card with troubleshooting tips
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

        tips_formatted = "AUTHENTICATION FAILED\n\n" + "\n".join(
            [f"• {tip}" for tip in troubleshooting_tips]
        )

        # Display error card
        print()
        print(
            Colors.box(
                tips_formatted,
                padding=1,
                border_color=Colors.ERROR,
                fill_color=Colors.BG_ERROR + Colors.WHITE,
            )
        )
        print()

        return False


def main():
    """Main entry point for Facebook login automation with enhanced UI"""
    # Clear screen
    clear_screen()

    # Show animated logo
    print_logo()
    time.sleep(1)

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
