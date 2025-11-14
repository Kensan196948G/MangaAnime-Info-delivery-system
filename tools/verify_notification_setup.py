#!/usr/bin/env python3
"""
Verification script for notification setup
Checks all required configuration for the test notification endpoint
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_mark(success):
    """Return a colored check mark or X"""
    return f"{GREEN}✓{RESET}" if success else f"{RED}✗{RESET}"

def print_header(text):
    """Print a formatted header"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text:^60}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def check_env_file():
    """Check if .env file exists and has required variables"""
    print_header("Checking .env File")

    env_path = Path('.env')

    if not env_path.exists():
        print(f"{check_mark(False)} .env file not found")
        return False

    print(f"{check_mark(True)} .env file exists")

    # Load environment variables
    load_dotenv()

    # Check required variables
    required_vars = {
        'GMAIL_APP_PASSWORD': 'Gmail app password (16 characters)',
        'GMAIL_ADDRESS or GMAIL_SENDER_EMAIL': 'Gmail sender address'
    }

    all_found = True

    # Check Gmail password
    gmail_password = os.getenv('GMAIL_APP_PASSWORD')
    if gmail_password:
        clean_password = gmail_password.replace(' ', '')
        if len(clean_password) == 16:
            print(f"{check_mark(True)} GMAIL_APP_PASSWORD is set (16 characters)")
        else:
            print(f"{check_mark(False)} GMAIL_APP_PASSWORD is set but has {len(clean_password)} characters (expected 16)")
            all_found = False
    else:
        print(f"{check_mark(False)} GMAIL_APP_PASSWORD is not set")
        all_found = False

    # Check Gmail address
    gmail_address = (
        os.getenv('GMAIL_ADDRESS') or
        os.getenv('GMAIL_SENDER_EMAIL') or
        os.getenv('GMAIL_RECIPIENT_EMAIL')
    )

    if gmail_address:
        print(f"{check_mark(True)} Gmail address is set: {gmail_address}")
    else:
        print(f"{check_mark(False)} Gmail address is not set (GMAIL_ADDRESS, GMAIL_SENDER_EMAIL, or GMAIL_RECIPIENT_EMAIL)")
        all_found = False

    return all_found

def check_config_file():
    """Check if config.json exists and has correct structure"""
    print_header("Checking config.json File")

    config_path = Path('config.json')

    if not config_path.exists():
        print(f"{check_mark(False)} config.json file not found")
        return False

    print(f"{check_mark(True)} config.json file exists")

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        print(f"{check_mark(True)} config.json is valid JSON")

        # Check structure
        if 'google' in config:
            print(f"{check_mark(True)} 'google' section exists")

            if 'gmail' in config['google']:
                print(f"{check_mark(True)} 'google.gmail' section exists")
                gmail_config = config['google']['gmail']

                if 'from_email' in gmail_config:
                    print(f"  - from_email: {gmail_config['from_email'] or '(empty)'}")
                if 'to_email' in gmail_config:
                    print(f"  - to_email: {gmail_config['to_email'] or '(empty)'}")
            else:
                print(f"{check_mark(False)} 'google.gmail' section is missing")
        else:
            print(f"{check_mark(False)} 'google' section is missing")

        return True

    except json.JSONDecodeError as e:
        print(f"{check_mark(False)} config.json is not valid JSON: {e}")
        return False
    except Exception as e:
        print(f"{check_mark(False)} Error reading config.json: {e}")
        return False

def check_dependencies():
    """Check if required Python packages are installed"""
    print_header("Checking Python Dependencies")

    required_packages = {
        'flask': 'Flask',
        'dotenv': 'python-dotenv',
        'requests': 'requests'
    }

    all_installed = True

    for import_name, package_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"{check_mark(True)} {package_name} is installed")
        except ImportError:
            print(f"{check_mark(False)} {package_name} is not installed")
            all_installed = False

    # Check built-in modules
    builtins = ['smtplib', 'ssl', 'email']
    for module in builtins:
        try:
            __import__(module)
            print(f"{check_mark(True)} {module} is available (built-in)")
        except ImportError:
            print(f"{check_mark(False)} {module} is not available")
            all_installed = False

    return all_installed

def check_web_app():
    """Check if web_app.py exists and is valid"""
    print_header("Checking web_app.py")

    web_app_path = Path('app/web_app.py')

    if not web_app_path.exists():
        print(f"{check_mark(False)} app/web_app.py not found")
        return False

    print(f"{check_mark(True)} app/web_app.py exists")

    # Check if it's valid Python
    try:
        with open(web_app_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check for the test notification endpoint
        if '@app.route("/api/test-notification"' in content:
            print(f"{check_mark(True)} /api/test-notification endpoint found")
        else:
            print(f"{check_mark(False)} /api/test-notification endpoint not found")
            return False

        # Check for improved error handling
        if 'force=True, silent=True' in content:
            print(f"{check_mark(True)} Enhanced JSON parsing detected")
        else:
            print(f"{YELLOW}⚠{RESET}  Enhanced JSON parsing not found (might be old version)")

        if 'SMTPAuthenticationError' in content:
            print(f"{check_mark(True)} Enhanced SMTP error handling detected")
        else:
            print(f"{YELLOW}⚠{RESET}  Enhanced SMTP error handling not found (might be old version)")

        return True

    except Exception as e:
        print(f"{check_mark(False)} Error reading web_app.py: {e}")
        return False

def print_summary(results):
    """Print a summary of all checks"""
    print_header("Summary")

    total = len(results)
    passed = sum(results.values())

    print(f"Total checks: {total}")
    print(f"Passed: {GREEN}{passed}{RESET}")
    print(f"Failed: {RED}{total - passed}{RESET}")
    print()

    if all(results.values()):
        print(f"{GREEN}✓ All checks passed! The notification system is properly configured.{RESET}")
        print(f"\n{BLUE}Next steps:{RESET}")
        print("1. Start the Flask application:")
        print("   python3 app/web_app.py")
        print("\n2. Test the notification endpoint:")
        print("   python3 /tmp/test_notification_endpoint.py")
        return 0
    else:
        print(f"{RED}✗ Some checks failed. Please fix the issues above.{RESET}")
        return 1

def main():
    """Main verification function"""
    # Change to project root if needed
    if not Path('config.json').exists():
        project_root = Path(__file__).parent.parent
        os.chdir(project_root)
        print(f"Changed directory to: {project_root}")

    results = {
        'Environment File': check_env_file(),
        'Config File': check_config_file(),
        'Dependencies': check_dependencies(),
        'Web Application': check_web_app()
    }

    return print_summary(results)

if __name__ == '__main__':
    sys.exit(main())
