"""
Moodle REST API Client for Django College ERP.

Wraps Moodle's Web Services REST API so every other module can call
high-level Python methods instead of crafting raw HTTP requests.

Moodle admin must enable:
  - core_user_create_users / core_user_get_users_by_field / core_user_update_users
  - core_course_create_courses / core_course_get_courses_by_field
  - enrol_manual_enrol_users / enrol_manual_unenrol_users
  - core_course_get_categories
  - gradereport_user_get_grade_items / gradereport_overview_get_course_grades
  - core_completion_get_course_completion_status
  - core_enrol_get_enrolled_users
  - mod_assign_get_assignments / mod_assign_get_submissions
  - mod_quiz_get_quizzes_by_courses

Generate a token at:
  Site admin → Plugins → Web services → Manage tokens
"""

import logging
import requests
import urllib3
from django.conf import settings

# Suppress SSL warnings if verification is disabled (dev mode)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger(__name__)


class MoodleAPIError(Exception):
    """Raised when Moodle returns an error payload."""

    def __init__(self, message, error_code=None, debug_info=None):
        super().__init__(message)
        self.error_code = error_code
        self.debug_info = debug_info


class MoodleClient:
    """Thin wrapper around the Moodle REST / Web-Services API."""

    # Moodle role shortnames → role ids (populated lazily or via config)
    ROLE_STUDENT = 5          # default Moodle "student"
    ROLE_EDITING_TEACHER = 3  # default Moodle "editingteacher"
    ROLE_TEACHER = 4          # default Moodle "teacher" (non-editing)
    ROLE_MANAGER = 1          # default Moodle "manager"

    def __init__(self, base_url=None, token=None):
        self.base_url = (base_url or getattr(settings, 'MOODLE_BASE_URL', '')).rstrip('/')
        self.token = token or getattr(settings, 'MOODLE_API_TOKEN', '')
        self.timeout = getattr(settings, 'MOODLE_API_TIMEOUT', 30)

        if not self.base_url or not self.token:
            logger.warning("Moodle integration is NOT configured (MOODLE_BASE_URL / MOODLE_API_TOKEN missing).")

    # ------------------------------------------------------------------
    # Low-level helpers
    # ------------------------------------------------------------------

    @property
    def _endpoint(self):
        return f"{self.base_url}/webservice/rest/server.php"

    def _call(self, function, **params):
        """Execute a single Moodle web-service function and return the JSON."""
        payload = {
            'wstoken': self.token,
            'wsfunction': function,
            'moodlewsrestformat': 'json',
        }
        payload.update(params)

        try:
            # Allow disabling SSL verification for dev/testing (MOODLE_VERIFY_SSL defaults to True)
            verify_ssl = getattr(settings, 'MOODLE_VERIFY_SSL', True)
            resp = requests.post(self._endpoint, data=payload, timeout=self.timeout, verify=verify_ssl)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error("Moodle API network error: %s", exc)
            raise MoodleAPIError(f"Network error contacting Moodle: {exc}") from exc

        data = resp.json()

        # Moodle returns {"exception": ..., "errorcode": ..., "message": ...} on error
        if isinstance(data, dict) and 'exception' in data:
            logger.error("Moodle API error: %s – %s", data.get('errorcode'), data.get('message'))
            raise MoodleAPIError(
                data.get('message', 'Unknown Moodle error'),
                error_code=data.get('errorcode'),
                debug_info=data.get('debuginfo'),
            )

        return data

    @property
    def is_configured(self):
        """Return True when both URL and token are present."""
        return bool(self.base_url and self.token)

    def test_connection(self):
        """Ping Moodle with core_webservice_get_site_info."""
        info = self._call('core_webservice_get_site_info')
        return {
            'sitename': info.get('sitename'),
            'siteurl': info.get('siteurl'),
            'username': info.get('username'),
            'fullname': info.get('fullname'),
            'version': info.get('release'),
            'functions': [f['name'] for f in info.get('functions', [])],
        }

    # ------------------------------------------------------------------
    # User Management
    # ------------------------------------------------------------------

    def create_user(self, username, email, firstname, lastname, password=None):
        """
        Create a Moodle user.  Returns the new Moodle user-id (int).
        If password is None a random one is generated server-side.
        """
        user = {
            'users[0][username]': username,
            'users[0][email]': email,
            'users[0][firstname]': firstname,
            'users[0][lastname]': lastname,
            'users[0][auth]': 'manual',
            'users[0][createpassword]': 1 if password is None else 0,
        }
        if password:
            user['users[0][password]'] = password

        result = self._call('core_user_create_users', **user)
        return result[0]['id']

    def get_user_by_email(self, email):
        """Return the Moodle user dict for a given email, or None."""
        result = self._call(
            'core_user_get_users_by_field',
            field='email',
            **{'values[0]': email},
        )
        return result[0] if result else None

    def get_user_by_username(self, username):
        """Return the Moodle user dict for a given username, or None."""
        result = self._call(
            'core_user_get_users_by_field',
            field='username',
            **{'values[0]': username},
        )
        return result[0] if result else None

    def update_user(self, moodle_user_id, **fields):
        """
        Update fields on an existing Moodle user.
        Accepted keyword args: email, firstname, lastname, suspended (0/1).
        """
        params = {f'users[0][{k}]': v for k, v in fields.items()}
        params['users[0][id]'] = moodle_user_id
        self._call('core_user_update_users', **params)

    def suspend_user(self, moodle_user_id):
        self.update_user(moodle_user_id, suspended=1)

    def unsuspend_user(self, moodle_user_id):
        self.update_user(moodle_user_id, suspended=0)

    # ------------------------------------------------------------------
    # Category Management
    # ------------------------------------------------------------------

    def create_category(self, name, parent_id=0, description=''):
        """Create a Moodle course category.  Returns the new category id."""
        result = self._call(
            'core_course_create_categories',
            **{
                'categories[0][name]': name,
                'categories[0][parent]': parent_id,
                'categories[0][description]': description,
            },
        )
        return result[0]['id']

    def get_categories(self):
        """Return all categories."""
        return self._call('core_course_get_categories')

    # ------------------------------------------------------------------
    # Course Management
    # ------------------------------------------------------------------

    def create_course(self, fullname, shortname, category_id, summary=''):
        """Create a Moodle course.  Returns the new course-id (int)."""
        result = self._call(
            'core_course_create_courses',
            **{
                'courses[0][fullname]': fullname,
                'courses[0][shortname]': shortname,
                'courses[0][categoryid]': category_id,
                'courses[0][summary]': summary,
                'courses[0][format]': 'topics',
                'courses[0][visible]': 1,
            },
        )
        return result[0]['id']

    def get_course_by_shortname(self, shortname):
        """Return the Moodle course dict or None."""
        result = self._call(
            'core_course_get_courses_by_field',
            field='shortname',
            value=shortname,
        )
        courses = result.get('courses', [])
        return courses[0] if courses else None

    def get_course_by_id(self, course_id):
        """Return the Moodle course dict or None."""
        result = self._call(
            'core_course_get_courses_by_field',
            field='id',
            value=course_id,
        )
        courses = result.get('courses', [])
        return courses[0] if courses else None

    # ------------------------------------------------------------------
    # Enrolment
    # ------------------------------------------------------------------

    def enrol_user(self, user_id, course_id, role_id=None):
        """Enrol a user in a Moodle course with the given role."""
        if role_id is None:
            role_id = self.ROLE_STUDENT
        self._call(
            'enrol_manual_enrol_users',
            **{
                'enrolments[0][roleid]': role_id,
                'enrolments[0][userid]': user_id,
                'enrolments[0][courseid]': course_id,
            },
        )

    def unenrol_user(self, user_id, course_id, role_id=None):
        """Remove a user's enrolment from a course."""
        if role_id is None:
            role_id = self.ROLE_STUDENT
        self._call(
            'enrol_manual_unenrol_users',
            **{
                'enrolments[0][roleid]': role_id,
                'enrolments[0][userid]': user_id,
                'enrolments[0][courseid]': course_id,
            },
        )

    def get_enrolled_users(self, course_id):
        """Return list of enrolled user dicts for a course."""
        return self._call('core_enrol_get_enrolled_users', courseid=course_id)

    # ------------------------------------------------------------------
    # Grades
    # ------------------------------------------------------------------

    def get_user_grades(self, course_id, user_id):
        """Return grade items for a single user in a course."""
        result = self._call(
            'gradereport_user_get_grade_items',
            courseid=course_id,
            userid=user_id,
        )
        return result.get('usergrades', [])

    def get_course_grades_overview(self, course_id):
        """Return all users' final grades for a course."""
        result = self._call(
            'gradereport_overview_get_course_grades',
            courseid=course_id,
        )
        return result.get('grades', [])

    # ------------------------------------------------------------------
    # Completion
    # ------------------------------------------------------------------

    def get_completion_status(self, course_id, user_id):
        """Return course completion status for a user."""
        result = self._call(
            'core_completion_get_course_completion_status',
            courseid=course_id,
            userid=user_id,
        )
        return result.get('completionstatus', {})

    # ------------------------------------------------------------------
    # Activities – Assignments & Quizzes
    # ------------------------------------------------------------------

    def get_assignments(self, course_ids):
        """Return assignment activities for the given course ids."""
        params = {f'courseids[{i}]': cid for i, cid in enumerate(course_ids)}
        result = self._call('mod_assign_get_assignments', **params)
        return result.get('courses', [])

    def get_submissions(self, assignment_ids):
        """Return submission data for the given assignment ids."""
        params = {f'assignmentids[{i}]': aid for i, aid in enumerate(assignment_ids)}
        result = self._call('mod_assign_get_submissions', **params)
        return result.get('assignments', [])

    def get_quizzes(self, course_ids):
        """Return quiz activities for the given course ids."""
        params = {f'courseids[{i}]': cid for i, cid in enumerate(course_ids)}
        result = self._call('mod_quiz_get_quizzes_by_courses', **params)
        return result.get('quizzes', [])


# ---------------------------------------------------------------------------
# Module-level singleton (lazy initialisation via Django settings)
# ---------------------------------------------------------------------------
_client = None


def get_moodle_client() -> MoodleClient:
    """Return a shared MoodleClient instance."""
    global _client
    if _client is None:
        _client = MoodleClient()
    return _client
