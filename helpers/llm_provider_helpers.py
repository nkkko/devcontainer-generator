import os


DEFAULT_LLM_PROVIDER = "azure_openai"
SUPPORTED_LLM_PROVIDERS = {"azure_openai", "openai"}


def get_llm_provider(provider=None):
    selected_provider = provider or os.getenv("LLM_PROVIDER", DEFAULT_LLM_PROVIDER)
    return selected_provider.strip().lower().replace("-", "_")


def is_supported_llm_provider(provider=None):
    return get_llm_provider(provider) in SUPPORTED_LLM_PROVIDERS


def required_env_vars_for_provider(provider=None):
    selected_provider = get_llm_provider(provider)
    if selected_provider == "azure_openai":
        return [
            "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_API_KEY",
            "AZURE_OPENAI_API_VERSION",
        ]
    if selected_provider == "openai":
        return ["OPENAI_API_KEY"]
    return ["LLM_PROVIDER"]
