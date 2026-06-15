import hashlib
import re


GITHUB_REPO_URL_PATTERN = re.compile(r"^https?://github\.com/[\w-]+/[\w.-]+/?$")
URL_PATTERN = re.compile(r"^[a-z][a-z0-9+.-]*://", re.IGNORECASE)


def normalize_project_description(description: str) -> str:
    lines = [" ".join(line.split()) for line in description.strip().splitlines()]
    return "\n".join(line for line in lines if line)


def is_project_description(value: str) -> bool:
    description = normalize_project_description(value)
    if len(description) < 10:
        return False
    if GITHUB_REPO_URL_PATTERN.match(description):
        return False
    return URL_PATTERN.match(description) is None


def build_project_description_context(description: str) -> str:
    description = normalize_project_description(description)
    if not is_project_description(description):
        raise ValueError("Please enter a GitHub repository URL or describe the project you want to generate.")

    return (
        "<<SECTION: Project Description >>\n"
        f"{description}\n"
        "<<END_SECTION: Project Description >>"
    )


def project_description_cache_key(description: str) -> str:
    description = normalize_project_description(description)
    digest = hashlib.sha256(description.encode("utf-8")).hexdigest()
    return f"description:{digest}"
