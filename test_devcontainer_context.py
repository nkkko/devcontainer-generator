import importlib
import os
import sys
import types
import unittest
from unittest.mock import patch


def import_devcontainer_helpers():
    fake_supabase_client = types.ModuleType("supabase_client")
    fake_supabase_client.supabase = object()
    sys.modules["supabase_client"] = fake_supabase_client
    sys.modules.pop("helpers.devcontainer_helpers", None)
    return importlib.import_module("helpers.devcontainer_helpers")


class DevcontainerContextTest(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("MODEL", None)
        os.environ.pop("LLM_MODEL_MAX_TOKENS", None)

    def test_generation_uses_llm_model_token_limit_from_env(self):
        helpers = import_devcontainer_helpers()
        os.environ["MODEL"] = "custom-chat-model"
        os.environ["LLM_MODEL_MAX_TOKENS"] = "7"

        captured = {}

        def fake_truncate_context(repo_context, model_name=None, max_tokens=None):
            captured["repo_context"] = repo_context
            captured["model_name"] = model_name
            captured["max_tokens"] = max_tokens
            return "truncated context"

        class Completion:
            def create(self, **kwargs):
                captured["model"] = kwargs["model"]
                captured["prompt"] = kwargs["messages"][1]["content"]
                return types.SimpleNamespace(
                    dict=lambda exclude_none=True: {"name": "example", "image": "python:3.12"}
                )

        instructor_client = types.SimpleNamespace(
            chat=types.SimpleNamespace(completions=Completion())
        )

        with patch.object(helpers, "truncate_context", side_effect=fake_truncate_context), \
                patch.object(helpers, "validate_devcontainer_json", return_value=True):
            devcontainer_json, devcontainer_url = helpers.generate_devcontainer_json(
                instructor_client,
                "https://github.com/example/repo",
                "full repository context",
            )

        self.assertIn('"name": "example"', devcontainer_json)
        self.assertIsNone(devcontainer_url)
        self.assertEqual(captured["repo_context"], "full repository context")
        self.assertEqual(captured["model_name"], "custom-chat-model")
        self.assertEqual(captured["max_tokens"], 7)
        self.assertEqual(captured["model"], "custom-chat-model")
        self.assertIn("truncated context", captured["prompt"])


if __name__ == "__main__":
    unittest.main()
