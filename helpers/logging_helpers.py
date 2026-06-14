import logging
import os


DEBUG_ENVIRONMENTS = {"dev", "development", "local", "test", "debug"}


def get_log_level(environment=None):
    app_env = environment
    if app_env is None:
        app_env = (
            os.getenv("APP_ENV")
            or os.getenv("ENVIRONMENT")
            or os.getenv("PYTHON_ENV")
            or os.getenv("ENV")
            or ""
        )

    return logging.DEBUG if app_env.lower() in DEBUG_ENVIRONMENTS else logging.INFO
