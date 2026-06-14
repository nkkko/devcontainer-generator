from dataclasses import dataclass
import re


CONTEXT_SECTION_PATTERN = re.compile(
    r"<<SECTION: (?P<title>.*?) >>\n(?P<body>.*?)(?:\n)?<<END_SECTION: (?P=title) >>",
    re.DOTALL,
)

HIGH_PRIORITY_FILES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "Cargo.toml",
    "Cargo.lock",
    "go.mod",
    "go.sum",
    "pom.xml",
    "build.gradle",
    "Dockerfile",
    "docker-compose.yml",
    "compose.yml",
    "Gemfile",
    "Pipfile",
    "Pipfile.lock",
    "setup.py",
    "Makefile",
    "CMakeLists.txt",
}

TRUNCATION_NOTICE = "\n\n<<TRUNCATED: Context window budget reached >>"


@dataclass
class ContextSection:
    title: str
    text: str
    order: int
    priority: int


def _encoding_for_context():
    import tiktoken

    return tiktoken.encoding_for_model("gpt-4o-mini")


def count_context_tokens(text, encoding=None):
    selected_encoding = encoding or _encoding_for_context()
    return len(selected_encoding.encode(text))


def _section_priority(title):
    normalized_title = title.strip()
    if normalized_title == "Repository Structure":
        return 0
    if normalized_title == "Repository Languages":
        return 1
    if normalized_title == "Existing devcontainer.json":
        return 2
    if normalized_title.startswith("Content of "):
        file_name = normalized_title.removeprefix("Content of ").strip()
        if file_name in HIGH_PRIORITY_FILES:
            return 3
        if file_name.lower() == "readme.md":
            return 4
    return 5


def _parse_context_sections(context):
    sections = []
    for order, match in enumerate(CONTEXT_SECTION_PATTERN.finditer(context)):
        title = match.group("title")
        sections.append(
            ContextSection(
                title=title,
                text=match.group(0),
                order=order,
                priority=_section_priority(title),
            )
        )
    return sections


def _truncate_text_to_budget(text, max_tokens, encoding):
    if max_tokens <= 0:
        return ""

    tokens = encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return encoding.decode(tokens[:max_tokens])


def _truncate_section_to_budget(section, max_tokens, encoding):
    notice_tokens = count_context_tokens(TRUNCATION_NOTICE, encoding)
    if max_tokens <= notice_tokens:
        return _truncate_text_to_budget(section.text, max_tokens, encoding)

    truncated = _truncate_text_to_budget(section.text, max_tokens - notice_tokens, encoding)
    if not truncated:
        return ""
    return truncated.rstrip() + TRUNCATION_NOTICE


def optimize_context_window(context, max_tokens=120000, encoding=None):
    selected_encoding = encoding or _encoding_for_context()
    initial_tokens = count_context_tokens(context, selected_encoding)

    if initial_tokens <= max_tokens:
        return context

    sections = _parse_context_sections(context)
    if not sections:
        return _truncate_text_to_budget(context, max_tokens, selected_encoding)

    selected_sections = []
    used_tokens = 0

    for section in sorted(sections, key=lambda item: (item.priority, item.order)):
        separator = "\n\n" if selected_sections else ""
        separator_tokens = count_context_tokens(separator, selected_encoding)
        section_tokens = count_context_tokens(section.text, selected_encoding)
        available_tokens = max_tokens - used_tokens - separator_tokens

        if available_tokens <= 0:
            break

        if section_tokens <= available_tokens:
            selected_sections.append(section.text)
            used_tokens += separator_tokens + section_tokens
            continue

        truncated_section = _truncate_section_to_budget(section, available_tokens, selected_encoding)
        if truncated_section:
            selected_sections.append(truncated_section)
        break

    optimized_context = "\n\n".join(selected_sections)
    optimized_tokens = count_context_tokens(optimized_context, selected_encoding)
    if optimized_tokens > max_tokens:
        return _truncate_text_to_budget(optimized_context, max_tokens, selected_encoding)

    return optimized_context
