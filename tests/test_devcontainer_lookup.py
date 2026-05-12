import unittest

from helpers.devcontainer_lookup import resolve_devcontainer_lookup


class ResolveDevcontainerLookupTests(unittest.TestCase):
    def test_cached_database_record_skips_repo_fetch_and_generation(self):
        calls = {"lookup": 0, "fetch": 0, "generate": 0}
        record = {
            "devcontainer_json": '{"name": "cached"}',
            "generated": True,
            "devcontainer_url": "https://example.com/devcontainer.json",
        }

        def check_url_exists(url):
            calls["lookup"] += 1
            return True, record

        def fetch_repo_context(url):
            calls["fetch"] += 1
            raise AssertionError("fetch_repo_context should not run for cache hits")

        def generate_devcontainer_json(*args, **kwargs):
            calls["generate"] += 1
            raise AssertionError("generate_devcontainer_json should not run for cache hits")

        result = resolve_devcontainer_lookup(
            "https://github.com/example/project",
            regenerate=False,
            instructor_client=object(),
            check_url_exists=check_url_exists,
            fetch_repo_context=fetch_repo_context,
            generate_devcontainer_json=generate_devcontainer_json,
        )

        self.assertEqual(result.devcontainer_json, record["devcontainer_json"])
        self.assertTrue(result.generated)
        self.assertEqual(result.source, "database")
        self.assertEqual(result.url, record["devcontainer_url"])
        self.assertFalse(result.should_save)
        self.assertEqual(calls, {"lookup": 1, "fetch": 0, "generate": 0})

    def test_missing_record_fetches_and_generates_devcontainer(self):
        calls = {"lookup": 0, "fetch": 0, "generate": 0}

        def check_url_exists(url):
            calls["lookup"] += 1
            return False, None

        def fetch_repo_context(url):
            calls["fetch"] += 1
            return "repo context", None, None

        def generate_devcontainer_json(
            client, url, repo_context, devcontainer_url, regenerate=False
        ):
            calls["generate"] += 1
            return '{"name": "generated"}', None

        result = resolve_devcontainer_lookup(
            "https://github.com/example/project",
            regenerate=False,
            instructor_client=object(),
            check_url_exists=check_url_exists,
            fetch_repo_context=fetch_repo_context,
            generate_devcontainer_json=generate_devcontainer_json,
        )

        self.assertEqual(result.devcontainer_json, '{"name": "generated"}')
        self.assertEqual(result.source, "generated")
        self.assertTrue(result.generated)
        self.assertTrue(result.should_save)
        self.assertEqual(result.repo_context, "repo context")
        self.assertIsNone(result.devcontainer_url)
        self.assertEqual(calls, {"lookup": 1, "fetch": 1, "generate": 1})

    def test_regenerate_ignores_cached_record_and_refreshes_context(self):
        calls = {"lookup": 0, "fetch": 0, "generate": 0}
        record = {
            "devcontainer_json": '{"name": "cached"}',
            "generated": True,
            "devcontainer_url": "https://example.com/devcontainer.json",
        }

        def check_url_exists(url):
            calls["lookup"] += 1
            return True, record

        def fetch_repo_context(url):
            calls["fetch"] += 1
            return "repo context", None, "https://example.com/source-devcontainer.json"

        def generate_devcontainer_json(
            client, url, repo_context, devcontainer_url, regenerate=False
        ):
            calls["generate"] += 1
            self.assertTrue(regenerate)
            return '{"name": "regenerated"}', None

        result = resolve_devcontainer_lookup(
            "https://github.com/example/project",
            regenerate=True,
            instructor_client=object(),
            check_url_exists=check_url_exists,
            fetch_repo_context=fetch_repo_context,
            generate_devcontainer_json=generate_devcontainer_json,
        )

        self.assertEqual(result.devcontainer_json, '{"name": "regenerated"}')
        self.assertEqual(result.source, "generated")
        self.assertTrue(result.generated)
        self.assertTrue(result.should_save)
        self.assertEqual(result.devcontainer_url, "https://example.com/source-devcontainer.json")
        self.assertEqual(calls, {"lookup": 1, "fetch": 1, "generate": 1})


if __name__ == "__main__":
    unittest.main()
