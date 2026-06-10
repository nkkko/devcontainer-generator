import os
import tiktoken

DEFAULT_ENCODING = "cl100k_base"
DEFAULT_LLM_MAX_TOKENS = 126000
DEFAULT_EMBEDDING_MAX_TOKENS = 8192


def encoding_for_model(model_name):
    try:
        return tiktoken.encoding_for_model(model_name)
    except KeyError:
        return tiktoken.get_encoding(DEFAULT_ENCODING)


def count_tokens(text):
    encoder = encoding_for_model("gpt-4o")
    tokens = encoder.encode(text)
    return len(tokens)


def max_tokens_from_env(env_name, default):
    try:
        default = int(default)
    except (TypeError, ValueError):
        default = DEFAULT_LLM_MAX_TOKENS

    raw_value = os.getenv(env_name)
    if not raw_value:
        return default

    try:
        max_tokens = int(raw_value)
    except ValueError:
        return default

    return max_tokens if max_tokens > 0 else default


def truncate_to_token_limit(text, model_name, max_tokens):
    encoding = encoding_for_model(model_name)
    tokens = encoding.encode(text)
    if len(tokens) > max_tokens:
        truncated_tokens = tokens[:max_tokens]
        return encoding.decode(truncated_tokens)
    return text
