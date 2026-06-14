import os
import logging
from openai import AzureOpenAI, OpenAI
import instructor

from helpers.llm_provider_helpers import get_llm_provider, is_supported_llm_provider, required_env_vars_for_provider

def setup_azure_openai():
    logging.info("Setting up Azure OpenAI client...")
    return AzureOpenAI(
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    )

def setup_openai():
    logging.info("Setting up OpenAI-compatible client...")
    return OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL") or None,
    )

def setup_llm_client():
    provider = get_llm_provider()
    if provider == "azure_openai":
        return setup_azure_openai()
    if provider == "openai":
        return setup_openai()
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

def setup_instructor(openai_client):
    logging.info("Setting up Instructor client...")
    return instructor.patch(openai_client)

def check_env_vars():
    if not is_supported_llm_provider():
        print(f"Unsupported LLM_PROVIDER: {get_llm_provider()}")
        return False

    required_vars = [
        "MODEL",
        "GITHUB_TOKEN",
    ]
    required_vars.extend(required_env_vars_for_provider())
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    if missing_vars:
        print(
            f"Missing environment variables: {', '.join(missing_vars)}. "
            "Please configure the env vars file properly."
        )
        return False
    return True
