from django.apps import AppConfig


class LmsIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lms_integration'
    verbose_name = 'LMS (Moodle) Integration'

    def ready(self):
        import lms_integration.signals  # noqa: F401
