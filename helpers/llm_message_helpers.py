import os


ANTHROPIC_PREFILL_ENV_VAR = "ANTHROPIC_PREFILL_PROMPT"
DEFAULT_ANTHROPIC_PREFILL_PROMPT = "{"


def is_anthropic_model(model_name):
    if not model_name:
        return False

    normalized_model = model_name.strip().lower()
    return normalized_model.startswith("claude") or (
        "anthropic" in normalized_model and "claude" in normalized_model
    )


def get_anthropic_prefill_prompt():
    configured_prefill = os.getenv(ANTHROPIC_PREFILL_ENV_VAR, DEFAULT_ANTHROPIC_PREFILL_PROMPT)
    return configured_prefill.strip() or DEFAULT_ANTHROPIC_PREFILL_PROMPT


def build_devcontainer_messages(prompt, model_name=None):
    messages = [
        {"role": "system", "content": "You are a helpful assistant that generates devcontainer.json files."},
        {"role": "user", "content": prompt},
    ]

    if is_anthropic_model(model_name):
        messages.append(
            {
                "role": "assistant",
                "content": get_anthropic_prefill_prompt(),
            }
        )

    return messages
