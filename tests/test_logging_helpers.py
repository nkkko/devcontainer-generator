import logging
import unittest

from helpers.logging_helpers import get_log_level


class LoggingHelpersTest(unittest.TestCase):
    def test_development_like_environments_use_debug_logging(self):
        for environment in ("dev", "development", "local", "test", "debug"):
            with self.subTest(environment=environment):
                self.assertEqual(get_log_level(environment), logging.DEBUG)

    def test_production_like_environments_use_info_logging(self):
        for environment in ("", "prod", "production", "staging"):
            with self.subTest(environment=environment):
                self.assertEqual(get_log_level(environment), logging.INFO)


if __name__ == "__main__":
    unittest.main()
