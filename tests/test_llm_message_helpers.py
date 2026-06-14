import os
import unittest
from unittest.mock import patch

from helpers.llm_message_helpers import build_devcontainer_messages, is_anthropic_model


class LlmMessageHelpersTest(unittest.TestCase):
    def test_non_anthropic_models_keep_original_messages(self):
        messages = build_devcontainer_messages("render this prompt", "gpt-4o-mini")

        self.assertEqual(
            messages,
            [
                {"role": "system", "content": "You are a helpful assistant that generates devcontainer.json files."},
                {"role": "user", "content": "render this prompt"},
            ],
        )

    def test_anthropic_models_add_default_prefill(self):
        messages = build_devcontainer_messages("render this prompt", "claude-3-5-sonnet-20241022")

        self.assertEqual(messages[-1], {"role": "assistant", "content": "{"})
        self.assertEqual(len(messages), 3)

    def test_anthropic_prefill_can_be_overridden(self):
        with patch.dict(os.environ, {"ANTHROPIC_PREFILL_PROMPT": '{"name":'}, clear=False):
            messages = build_devcontainer_messages("render this prompt", "anthropic/claude-3-haiku")

        self.assertEqual(messages[-1], {"role": "assistant", "content": '{"name":'})

    def test_anthropic_model_detection_requires_claude_context(self):
        self.assertTrue(is_anthropic_model("claude-3-opus"))
        self.assertTrue(is_anthropic_model("anthropic/claude-3-haiku"))
        self.assertFalse(is_anthropic_model("gpt-4o-mini"))
        self.assertFalse(is_anthropic_model("some-anthropic-compatible-model"))


if __name__ == "__main__":
    unittest.main()
