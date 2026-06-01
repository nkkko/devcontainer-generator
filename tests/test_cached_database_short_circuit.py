import asyncio
import importlib.util
import sys
import types
from pathlib import Path


def _tag(name):
    def render(*children, **attrs):
        return {"tag": name, "children": children, "attrs": attrs}

    return render


def load_main_module(monkeypatch):
    """Import main.py with lightweight stand-ins for optional app dependencies."""
    repo_root = Path(__file__).resolve().parents[1]

    for module_name in [
        "main_under_test",
        "fasthtml",
        "fasthtml.common",
        "fastcore",
        "fastcore.xtras",
        "content",
        "supabase_client",
        "helpers.openai_helpers",
        "helpers.github_helpers",
        "helpers.devcontainer_helpers",
        "helpers.token_helpers",
    ]:
        sys.modules.pop(module_name, None)

    common = types.ModuleType("fasthtml.common")
    for name in [
        "Script",
        "Meta",
        "Link",
        "Title",
        "Main",
        "Div",
        "Article",
        "Pre",
        "Code",
        "Button",
        "Img",
        "Span",
        "H2",
        "P",
        "FileResponse",
    ]:
        setattr(common, name, _tag(name))

    common.picolink = _tag("picolink")
    common.scopesrc = _tag("scopesrc")
    common.Favicon = lambda *args, **kwargs: (_tag("Favicon")(*args, **kwargs),)
    common.Socials = lambda *args, **kwargs: (_tag("Socials")(*args, **kwargs),)
    common.serve = lambda *args, **kwargs: None

    def fast_app(*args, **kwargs):
        def rt(*route_args, **route_kwargs):
            def decorator(func):
                return func

            return decorator

        return object(), rt

    common.fast_app = fast_app
    fasthtml = types.ModuleType("fasthtml")
    fasthtml.common = common
    monkeypatch.setitem(sys.modules, "fasthtml", fasthtml)
    monkeypatch.setitem(sys.modules, "fasthtml.common", common)

    xtras = types.ModuleType("fastcore.xtras")
    xtras.timed_cache = lambda seconds=60: (lambda func: func)
    fastcore = types.ModuleType("fastcore")
    fastcore.xtras = xtras
    monkeypatch.setitem(sys.modules, "fastcore", fastcore)
    monkeypatch.setitem(sys.modules, "fastcore.xtras", xtras)

    content = types.ModuleType("content")
    content.description = "test description"
    content.picolink = _tag("picolink")
    content.scopesrc = _tag("scopesrc")
    for name in [
        "hero_section",
        "generator_section",
        "setup_section",
        "manifesto",
        "benefits_section",
        "examples_section",
        "faq_section",
        "cta_section",
        "footer_section",
        "manifesto_page",
    ]:
        setattr(content, name, _tag(name))
    monkeypatch.setitem(sys.modules, "content", content)

    supabase_client = types.ModuleType("supabase_client")
    supabase_client.supabase = object()
    monkeypatch.setitem(sys.modules, "supabase_client", supabase_client)

    openai_helpers = types.ModuleType("helpers.openai_helpers")
    openai_helpers.setup_azure_openai = lambda: object()
    openai_helpers.setup_instructor = lambda client: object()
    monkeypatch.setitem(sys.modules, "helpers.openai_helpers", openai_helpers)

    github_helpers = types.ModuleType("helpers.github_helpers")
    github_helpers.fetch_repo_context = lambda repo_url: ("repo context", None, None)
    github_helpers.check_url_exists = lambda repo_url: (False, None)
    monkeypatch.setitem(sys.modules, "helpers.github_helpers", github_helpers)

    devcontainer_helpers = types.ModuleType("helpers.devcontainer_helpers")
    devcontainer_helpers.generate_devcontainer_json = lambda *args, **kwargs: ('{}', None)
    devcontainer_helpers.validate_devcontainer_json = lambda devcontainer_json: True
    monkeypatch.setitem(sys.modules, "helpers.devcontainer_helpers", devcontainer_helpers)

    token_helpers = types.ModuleType("helpers.token_helpers")
    token_helpers.count_tokens = lambda text: len(text.split())
    token_helpers.truncate_to_token_limit = lambda text, *args, **kwargs: text
    monkeypatch.setitem(sys.modules, "helpers.token_helpers", token_helpers)

    spec = importlib.util.spec_from_file_location("main_under_test", repo_root / "main.py")
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, "main_under_test", module)
    spec.loader.exec_module(module)
    return module


def test_cached_database_result_skips_repo_fetch(monkeypatch):
    main = load_main_module(monkeypatch)
    calls = {"fetch_repo_context": 0, "generate_devcontainer_json": 0}

    cached_record = {
        "devcontainer_json": '{"name": "cached-devcontainer"}',
        "generated": True,
        "devcontainer_url": "https://example.com/.devcontainer/devcontainer.json",
    }

    monkeypatch.setattr(main, "check_url_exists", lambda repo_url: (True, cached_record))

    def fetch_repo_context(repo_url):
        calls["fetch_repo_context"] += 1
        return "repo context", None, None

    def generate_devcontainer_json(*args, **kwargs):
        calls["generate_devcontainer_json"] += 1
        return '{"name": "generated-devcontainer"}', None

    monkeypatch.setattr(main, "fetch_repo_context", fetch_repo_context)
    monkeypatch.setattr(main, "generate_devcontainer_json", generate_devcontainer_json)

    result = asyncio.run(main.post("https://github.com/daytonaio/devcontainer-generator/"))

    assert calls == {"fetch_repo_context": 0, "generate_devcontainer_json": 0}
    assert result["tag"] == "Div"
    assert "database" in result["children"][0]["children"][0]
