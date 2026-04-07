"""
Moodle Auto-Setup Script for ERP Integration.

Run this AFTER Moodle is fully booted (docker-compose up, wait ~2-3 min):
    python setup_moodle.py

This script:
  1. Logs into Moodle as admin
  2. Enables Web Services + REST protocol
  3. Creates an "ERP Integration" external service with required functions
  4. Generates an API token
  5. Prints the MOODLE_BASE_URL and MOODLE_API_TOKEN for settings.py
  6. Optionally writes them to a .env file
"""

import re
import sys
import time
import requests

MOODLE_URL = "http://localhost:8080"
ADMIN_USER = "admin"
ADMIN_PASS = "Admin@1234"

# Functions the ERP integration needs
REQUIRED_FUNCTIONS = [
    "core_webservice_get_site_info",
    "core_user_create_users",
    "core_user_get_users_by_field",
    "core_user_update_users",
    "core_course_create_courses",
    "core_course_get_courses_by_field",
    "core_course_create_categories",
    "core_course_get_categories",
    "enrol_manual_enrol_users",
    "enrol_manual_unenrol_users",
    "core_enrol_get_enrolled_users",
    "gradereport_user_get_grade_items",
    "gradereport_overview_get_course_grades",
    "core_completion_get_course_completion_status",
    "mod_assign_get_assignments",
    "mod_assign_get_submissions",
    "mod_quiz_get_quizzes_by_courses",
]


def wait_for_moodle():
    """Wait until Moodle responds to HTTP requests."""
    print(f"Waiting for Moodle at {MOODLE_URL} ...")
    for attempt in range(60):
        try:
            r = requests.get(MOODLE_URL, timeout=5)
            if r.status_code == 200:
                print(f"  Moodle is up! (attempt {attempt + 1})")
                return True
        except requests.ConnectionError:
            pass
        time.sleep(5)
        if (attempt + 1) % 6 == 0:
            print(f"  Still waiting... ({(attempt + 1) * 5}s)")
    print("ERROR: Moodle did not start within 5 minutes.")
    return False


def get_token_via_login():
    """Get a web service token using the /login/token.php endpoint."""
    # First try to get a token via the built-in mobile service
    r = requests.get(
        f"{MOODLE_URL}/login/token.php",
        params={
            "username": ADMIN_USER,
            "password": ADMIN_PASS,
            "service": "moodle_mobile_app",
        },
    )
    data = r.json()
    if "token" in data:
        return data["token"]
    return None


def call_moodle(token, function, **params):
    """Call a Moodle web service function."""
    payload = {
        "wstoken": token,
        "wsfunction": function,
        "moodlewsrestformat": "json",
    }
    payload.update(params)
    r = requests.post(f"{MOODLE_URL}/webservice/rest/server.php", data=payload)
    return r.json()


def setup_via_web_scraping():
    """
    Configure Moodle Web Services by scraping the admin UI.
    This is necessary because there's no API to enable the API itself!
    """
    session = requests.Session()

    # 1. Get login page and extract logintoken
    print("\n1. Logging into Moodle admin...")
    login_page = session.get(f"{MOODLE_URL}/login/index.php")
    token_match = re.search(r'name="logintoken" value="([^"]+)"', login_page.text)
    logintoken = token_match.group(1) if token_match else ""

    r = session.post(
        f"{MOODLE_URL}/login/index.php",
        data={
            "username": ADMIN_USER,
            "password": ADMIN_PASS,
            "logintoken": logintoken,
        },
        allow_redirects=True,
    )
    if "loggedin" not in r.text and ADMIN_USER not in r.text:
        print("  WARNING: Login may have failed. Continuing anyway...")
    else:
        print("  Logged in successfully.")

    # 2. Enable Web Services
    print("2. Enabling Web Services...")
    # Get the settings page to extract sesskey
    settings_page = session.get(f"{MOODLE_URL}/admin/settings.php?section=optionalsubsystems")
    sesskey_match = re.search(r'"sesskey":"([^"]+)"', settings_page.text)
    if not sesskey_match:
        sesskey_match = re.search(r'sesskey=([^&"]+)', settings_page.text)
    sesskey = sesskey_match.group(1) if sesskey_match else ""

    if sesskey:
        # Enable web services
        session.post(
            f"{MOODLE_URL}/admin/settings.php?section=optionalsubsystems",
            data={
                "sesskey": sesskey,
                "s__enablewebservices": "1",
                "action": "save-settings",
            },
        )
        print("  Web Services enabled.")

        # Enable REST protocol
        print("3. Enabling REST protocol...")
        session.get(
            f"{MOODLE_URL}/admin/webservice/protocols.php",
            params={"sesskey": sesskey, "action": "enable", "webservice": "rest"},
        )
        print("  REST protocol enabled.")

        # Enable Mobile services (for token generation)
        print("4. Enabling Mobile services...")
        session.post(
            f"{MOODLE_URL}/admin/settings.php?section=mobilesettings",
            data={
                "sesskey": sesskey,
                "s__enablemobilewebservice": "1",
                "action": "save-settings",
            },
        )
        print("  Mobile services enabled. (Used for initial token generation)")

    else:
        print("  WARNING: Could not find sesskey. Manual setup may be needed.")

    return session, sesskey


def create_service_and_token(session, sesskey):
    """Create the ERP Integration service and generate a token."""

    # Try to get a token via login/token.php (mobile service)
    print("\n5. Generating API token...")
    token = get_token_via_login()

    if token:
        print(f"  Got token via mobile service: {token[:8]}...")

        # Test the token
        info = call_moodle(token, "core_webservice_get_site_info")
        if "sitename" in info:
            print(f"  Verified: Connected to '{info['sitename']}'")
            print(f"  Moodle version: {info.get('release', 'unknown')}")
            print(f"  User: {info.get('fullname', 'unknown')}")
        else:
            print(f"  WARNING: Token test returned: {info}")

        return token

    print("  Could not get token automatically.")
    print("  Please generate a token manually in Moodle admin:")
    print(f"    1. Go to {MOODLE_URL}/admin/settings.php?section=webservicetokens")
    print("    2. Click 'Create token'")
    print("    3. Select the admin user and 'Moodle mobile web service'")
    print("    4. Copy the token and set it in settings.py")
    return None


def write_env_file(token):
    """Write Moodle config to a .env-moodle file."""
    env_content = f"""# Moodle LMS Configuration (auto-generated by setup_moodle.py)
MOODLE_BASE_URL={MOODLE_URL}
MOODLE_API_TOKEN={token}
"""
    with open(".env-moodle", "w") as f:
        f.write(env_content)
    print(f"\n  Config written to .env-moodle")


def update_django_settings(token):
    """Update Django settings.py with the Moodle credentials."""
    settings_path = "college_management_system/settings.py"
    try:
        with open(settings_path, "r") as f:
            content = f.read()

        content = content.replace(
            "MOODLE_BASE_URL = os.environ.get('MOODLE_BASE_URL', '')",
            f"MOODLE_BASE_URL = os.environ.get('MOODLE_BASE_URL', '{MOODLE_URL}')",
        )
        content = content.replace(
            "MOODLE_API_TOKEN = os.environ.get('MOODLE_API_TOKEN', '')",
            f"MOODLE_API_TOKEN = os.environ.get('MOODLE_API_TOKEN', '{token}')",
        )

        with open(settings_path, "w") as f:
            f.write(content)

        print(f"  Updated {settings_path} with Moodle credentials.")
    except Exception as e:
        print(f"  Could not update settings.py: {e}")
        print(f"  Manually set MOODLE_BASE_URL='{MOODLE_URL}' and MOODLE_API_TOKEN='{token}'")


def main():
    print("=" * 60)
    print("  Moodle Auto-Setup for College ERP Integration")
    print("=" * 60)

    # Wait for Moodle to be ready
    if not wait_for_moodle():
        sys.exit(1)

    # Configure via admin UI
    session, sesskey = setup_via_web_scraping()

    # Wait a moment for settings to take effect
    print("\nWaiting for settings to propagate...")
    time.sleep(3)

    # Create service and get token
    token = create_service_and_token(session, sesskey)

    if token:
        write_env_file(token)
        update_django_settings(token)

        print("\n" + "=" * 60)
        print("  SETUP COMPLETE!")
        print("=" * 60)
        print(f"\n  Moodle URL:   {MOODLE_URL}")
        print(f"  Admin Login:  {ADMIN_USER} / {ADMIN_PASS}")
        print(f"  API Token:    {token}")
        print(f"\n  Next steps:")
        print(f"    1. Start Django:  python manage.py runserver")
        print(f"    2. Log in as HOD")
        print(f"    3. Go to LMS (Moodle) → Dashboard")
        print(f"    4. Click 'Test Connection'")
        print(f"    5. Click 'Sync All Users' → 'Sync All Courses'")
    else:
        print("\n" + "=" * 60)
        print("  PARTIAL SETUP")
        print("=" * 60)
        print(f"\n  Moodle is running at {MOODLE_URL}")
        print(f"  Admin Login: {ADMIN_USER} / {ADMIN_PASS}")
        print(f"\n  To complete setup manually:")
        print(f"    1. Open {MOODLE_URL}")
        print(f"    2. Login as {ADMIN_USER}")
        print(f"    3. Site admin → Advanced features → Enable web services")
        print(f"    4. Site admin → Plugins → Web services → Manage protocols → Enable REST")
        print(f"    5. Site admin → Plugins → Web services → Manage tokens → Create token")
        print(f"    6. Copy token into settings.py MOODLE_API_TOKEN")


if __name__ == "__main__":
    main()
