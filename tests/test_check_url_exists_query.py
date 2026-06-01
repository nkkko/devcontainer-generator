import importlib
import sys
import types


class FakeQuery:
    def __init__(self):
        self.selected_columns = None
        self.filters = []
        self.order_args = None
        self.limit_value = None

    def select(self, columns):
        self.selected_columns = columns
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def order(self, column, desc=False):
        self.order_args = (column, desc)
        return self

    def limit(self, value):
        self.limit_value = value
        return self

    def execute(self):
        return types.SimpleNamespace(
            data=[
                {
                    "devcontainer_json": '{"name": "cached"}',
                    "generated": True,
                    "devcontainer_url": "https://example.com/devcontainer.json",
                    "created_at": "2024-01-01T00:00:00",
                }
            ]
        )


class FakeSupabase:
    def __init__(self):
        self.query = FakeQuery()
        self.table_name = None

    def table(self, table_name):
        self.table_name = table_name
        return self.query


def test_check_url_exists_selects_only_fields_needed_for_cached_response(monkeypatch):
    fake_supabase = FakeSupabase()

    supabase_client = types.ModuleType("supabase_client")
    supabase_client.supabase = fake_supabase
    monkeypatch.setitem(sys.modules, "supabase_client", supabase_client)

    token_helpers = types.ModuleType("helpers.token_helpers")
    token_helpers.count_tokens = lambda text: len(text.split())
    monkeypatch.setitem(sys.modules, "helpers.token_helpers", token_helpers)

    sys.modules.pop("helpers.github_helpers", None)
    github_helpers = importlib.import_module("helpers.github_helpers")

    exists, record = github_helpers.check_url_exists("https://github.com/daytonaio/devcontainer-generator")

    assert exists is True
    assert record["devcontainer_json"] == '{"name": "cached"}'
    assert fake_supabase.table_name == "devcontainers"
    assert fake_supabase.query.selected_columns == "devcontainer_json,generated,devcontainer_url,created_at"
    assert fake_supabase.query.filters == [("url", "https://github.com/daytonaio/devcontainer-generator")]
    assert fake_supabase.query.order_args == ("created_at", True)
    assert fake_supabase.query.limit_value == 1
