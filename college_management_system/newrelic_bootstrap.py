import os
from pathlib import Path


_INITIALIZED = False


def initialize_newrelic():
    global _INITIALIZED

    if _INITIALIZED:
        return

    if os.environ.get('NEW_RELIC_ENABLED', '').lower() in {'0', 'false', 'no', 'off'}:
        return

    config_file = os.environ.get('NEW_RELIC_CONFIG_FILE')

    if config_file:
        config_path = Path(config_file)
        if not config_path.exists():
            return
    else:
        config_path = Path(__file__).resolve().parent.parent / 'newrelic.ini'
        if not config_path.exists():
            return
        config_file = str(config_path)
        os.environ['NEW_RELIC_CONFIG_FILE'] = config_file

    try:
        import newrelic.agent
    except ImportError:
        return

    newrelic.agent.initialize(config_file, os.environ.get('NEW_RELIC_ENVIRONMENT'))
    _INITIALIZED = True
