import hashlib
import unittest

from helpers.natural_language_helpers import (
    build_project_description_context,
    is_project_description,
    normalize_project_description,
    project_description_cache_key,
)


class NaturalLanguageHelpersTest(unittest.TestCase):
    def test_normalize_project_description_collapses_line_spacing(self):
        description = "  Python   FastAPI service  \n\n  with Postgres and Redis  "

        self.assertEqual(
            normalize_project_description(description),
            "Python FastAPI service\nwith Postgres and Redis",
        )

    def test_detects_descriptions_without_accepting_urls(self):
        self.assertTrue(is_project_description("Node.js API with Redis and background workers"))
        self.assertFalse(is_project_description("https://github.com/daytonaio/daytona"))
        self.assertFalse(is_project_description("https://example.com/not-a-github-repo"))
        self.assertFalse(is_project_description("tiny"))

    def test_build_project_description_context_uses_expected_sections(self):
        context = build_project_description_context("Ruby on Rails app with PostgreSQL")

        self.assertIn("<<SECTION: Project Description >>", context)
        self.assertIn("Ruby on Rails app with PostgreSQL", context)
        self.assertIn("<<END_SECTION: Project Description >>", context)

    def test_project_description_cache_key_is_stable_for_normalized_text(self):
        description = "Python   FastAPI service\nwith Redis"
        normalized = "Python FastAPI service\nwith Redis"
        expected = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

        self.assertEqual(project_description_cache_key(description), f"description:{expected}")


if __name__ == "__main__":
    unittest.main()
