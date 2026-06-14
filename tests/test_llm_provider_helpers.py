import unittest

from helpers.llm_provider_helpers import get_llm_provider, is_supported_llm_provider, required_env_vars_for_provider


class LlmProviderHelpersTest(unittest.TestCase):
    def test_provider_names_are_normalized(self):
        self.assertEqual(get_llm_provider("azure-openai"), "azure_openai")
        self.assertEqual(get_llm_provider(" OpenAI "), "openai")

    def test_azure_openai_requires_azure_environment(self):
        self.assertEqual(
            required_env_vars_for_provider("azure_openai"),
            [
                "AZURE_OPENAI_ENDPOINT",
                "AZURE_OPENAI_API_KEY",
                "AZURE_OPENAI_API_VERSION",
            ],
        )

    def test_openai_compatible_provider_requires_openai_key(self):
        self.assertEqual(required_env_vars_for_provider("openai"), ["OPENAI_API_KEY"])

    def test_unknown_provider_reports_llm_provider_as_missing(self):
        self.assertEqual(required_env_vars_for_provider("anthropic"), ["LLM_PROVIDER"])

    def test_supported_provider_check(self):
        self.assertTrue(is_supported_llm_provider("azure_openai"))
        self.assertTrue(is_supported_llm_provider("openai"))
        self.assertFalse(is_supported_llm_provider("anthropic"))


if __name__ == "__main__":
    unittest.main()
