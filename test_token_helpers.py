import os
import unittest

from helpers.token_helpers import (
    DEFAULT_EMBEDDING_MAX_TOKENS,
    encoding_for_model,
    max_tokens_from_env,
    truncate_to_token_limit,
)


class TokenHelpersTest(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("TEST_MAX_TOKENS", None)

    def test_unknown_model_uses_fallback_encoding(self):
        encoding = encoding_for_model("unknown-provider/new-chat-model")

        self.assertGreater(len(encoding.encode("hello world")), 0)

    def test_max_tokens_from_env_uses_positive_integer(self):
        os.environ["TEST_MAX_TOKENS"] = "4096"

        self.assertEqual(max_tokens_from_env("TEST_MAX_TOKENS", DEFAULT_EMBEDDING_MAX_TOKENS), 4096)

    def test_max_tokens_from_env_uses_default_for_invalid_values(self):
        os.environ["TEST_MAX_TOKENS"] = "not-a-number"

        self.assertEqual(
            max_tokens_from_env("TEST_MAX_TOKENS", DEFAULT_EMBEDDING_MAX_TOKENS),
            DEFAULT_EMBEDDING_MAX_TOKENS,
        )

    def test_truncate_to_token_limit_supports_unknown_model_names(self):
        text = "one two three four"

        truncated = truncate_to_token_limit(text, "custom-embedding-model", 2)

        self.assertLessEqual(len(encoding_for_model("custom-embedding-model").encode(truncated)), 2)


if __name__ == "__main__":
    unittest.main()
