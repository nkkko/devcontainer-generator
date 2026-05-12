from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Tuple


@dataclass(frozen=True)
class DevcontainerLookupResult:
    devcontainer_json: str
    generated: bool
    source: str
    url: Optional[str]
    repo_context: Optional[str] = None
    devcontainer_url: Optional[str] = None
    should_save: bool = False


def resolve_devcontainer_lookup(
    repo_url: str,
    regenerate: bool,
    instructor_client: Any,
    check_url_exists: Callable[[str], Tuple[bool, Optional[Mapping[str, Any]]]],
    fetch_repo_context: Callable[[str], Tuple[str, Optional[str], Optional[str]]],
    generate_devcontainer_json: Callable[..., Tuple[str, Optional[str]]],
) -> DevcontainerLookupResult:
    exists, existing_record = check_url_exists(repo_url)

    if exists and existing_record and not regenerate:
        return DevcontainerLookupResult(
            devcontainer_json=existing_record["devcontainer_json"],
            generated=existing_record["generated"],
            source="database",
            url=existing_record["devcontainer_url"],
        )

    repo_context, _existing_devcontainer, devcontainer_url = fetch_repo_context(repo_url)
    devcontainer_json, url = generate_devcontainer_json(
        instructor_client,
        repo_url,
        repo_context,
        devcontainer_url,
        regenerate=regenerate,
    )

    return DevcontainerLookupResult(
        devcontainer_json=devcontainer_json,
        generated=True,
        source="generated" if url is None else "repository",
        url=url,
        repo_context=repo_context,
        devcontainer_url=devcontainer_url,
        should_save=True,
    )
