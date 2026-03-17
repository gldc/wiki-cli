"""Unit tests for wiki-cli core modules.

All tests use synthetic data — no network access required.
"""

import json
import os
import tempfile

import pytest


# ── Session Tests ────────────────────────────────────────────────────


class TestSession:
    """Tests for Session module."""

    def test_create_session(self):
        from wiki_cli.core.session import Session

        s = Session()
        assert s.current_page_id is None
        assert s.current_locale == "en"
        assert not s.modified

    def test_record_operation(self):
        from wiki_cli.core.session import Session

        s = Session()
        s.record("page_create", "Created page 'test'", {"page_id": 1})
        assert len(s._history) == 1
        assert s._history[0].op_type == "page_create"
        assert s.modified

    def test_undo(self):
        from wiki_cli.core.session import Session

        s = Session()
        s.record("page_create", "Created page", {"page_id": 1})
        op = s.undo()
        assert op is not None
        assert op.op_type == "page_create"
        assert len(s._history) == 0
        assert len(s._redo_stack) == 1

    def test_redo(self):
        from wiki_cli.core.session import Session

        s = Session()
        s.record("page_create", "Created page", {"page_id": 1})
        s.undo()
        op = s.redo()
        assert op is not None
        assert op.op_type == "page_create"
        assert len(s._history) == 1
        assert len(s._redo_stack) == 0

    def test_undo_empty(self):
        from wiki_cli.core.session import Session

        s = Session()
        assert s.undo() is None

    def test_redo_empty(self):
        from wiki_cli.core.session import Session

        s = Session()
        assert s.redo() is None

    def test_clear_history(self):
        from wiki_cli.core.session import Session

        s = Session()
        s.record("op1", "first")
        s.record("op2", "second")
        s.clear_history()
        assert len(s._history) == 0

    def test_history_limit(self):
        from wiki_cli.core.session import Session

        s = Session()
        for i in range(10):
            s.record("op", f"op {i}")
        history = s.history(limit=5)
        assert len(history) == 5

    def test_save_load_roundtrip(self):
        from wiki_cli.core.session import Session

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            s1 = Session()
            s1.url = "http://localhost:3000"
            s1.current_page_id = 42
            s1.current_page_path = "docs/guide"
            s1.record("page_create", "Created page", {"page_id": 42})
            s1.save(path)

            s2 = Session(session_path=path)
            assert s2.url == "http://localhost:3000"
            assert s2.current_page_id == 42
            assert s2.current_page_path == "docs/guide"
            assert len(s2._history) == 1
        finally:
            os.unlink(path)

    def test_status_dict(self):
        from wiki_cli.core.session import Session

        s = Session()
        s.current_locale = "fr"
        status = s.status()
        assert status["current_locale"] == "fr"
        assert status["history_count"] == 0

    def test_record_clears_redo(self):
        from wiki_cli.core.session import Session

        s = Session()
        s.record("op1", "first")
        s.undo()
        assert len(s._redo_stack) == 1
        s.record("op2", "second")
        assert len(s._redo_stack) == 0


# ── Backend Tests ────────────────────────────────────────────────────


class TestBackend:
    """Tests for wiki_backend module."""

    def test_load_config_default(self):
        from wiki_cli.utils.wiki_backend import load_config

        config = load_config("/nonexistent/path/config.json")
        assert "url" in config
        assert "api_key" in config

    def test_load_config_env_override(self, monkeypatch):
        from wiki_cli.utils.wiki_backend import load_config

        monkeypatch.setenv("WIKI_URL", "http://test:3000")
        monkeypatch.setenv("WIKI_API_KEY", "test-key-123")
        config = load_config("/nonexistent/path/config.json")
        assert config["url"] == "http://test:3000"
        assert config["api_key"] == "test-key-123"

    def test_save_and_reload_config(self):
        from wiki_cli.utils.wiki_backend import save_config, load_config

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_config("http://wiki:3000", "my-key", config_path=path)
            config = load_config(config_path=path)
            assert config["url"] == "http://wiki:3000"
            assert config["api_key"] == "my-key"
        finally:
            os.unlink(path)

    def test_validate_config_missing_url(self):
        from wiki_cli.utils.wiki_backend import validate_config

        with pytest.raises(RuntimeError, match="URL not configured"):
            validate_config({"url": "", "api_key": "key"})

    def test_validate_config_missing_key(self):
        from wiki_cli.utils.wiki_backend import validate_config

        with pytest.raises(RuntimeError, match="API key not configured"):
            validate_config({"url": "http://x", "api_key": ""})

    def test_client_init(self):
        from wiki_cli.utils.wiki_backend import WikiClient

        client = WikiClient(url="http://localhost:3000", api_key="test-key")
        assert client.graphql_url == "http://localhost:3000/graphql"
        assert client.api_key == "test-key"

    def test_client_url_strip_trailing_slash(self):
        from wiki_cli.utils.wiki_backend import WikiClient

        client = WikiClient(url="http://localhost:3000/", api_key="key")
        assert client.url == "http://localhost:3000"
        assert client.graphql_url == "http://localhost:3000/graphql"


# ── Page Module Tests ────────────────────────────────────────────────


class TestPageModule:
    """Tests for page module query/mutation strings."""

    def test_query_strings_not_empty(self):
        from wiki_cli.core import page

        assert len(page.Q_PAGE_LIST) > 50
        assert len(page.Q_PAGE_SINGLE) > 50
        assert len(page.M_PAGE_CREATE) > 50
        assert "pages" in page.Q_PAGE_LIST

    def test_update_page_field_map(self):
        """Verify update_page builds correct variables."""
        # We can't call update_page without a client, but we can verify
        # the function exists and has the right signature
        from wiki_cli.core.page import update_page
        import inspect

        sig = inspect.signature(update_page)
        assert "page_id" in sig.parameters
        assert "kwargs" in str(sig)


# ── Export Module Tests ──────────────────────────────────────────────


class TestExportModule:
    """Tests for export module with synthetic data."""

    def _mock_client(self, page_data):
        """Create a mock client that returns page_data for any query."""

        class MockClient:
            def execute(self, query, variables=None):
                return {"pages": {"single": page_data}}

        return MockClient()

    def test_export_markdown(self):
        from wiki_cli.core.export import export_page_markdown

        page = {
            "title": "Test Page",
            "content": "# Hello\nWorld",
            "description": "A test",
            "path": "test",
            "locale": "en",
            "tags": ["test"],
            "editor": "markdown",
        }
        client = self._mock_client(page)
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            path = f.name
        try:
            result = export_page_markdown(client, 1, path, overwrite=True)
            assert result["status"] == "ok"
            assert result["format"] == "markdown"
            assert os.path.exists(path)
            content = open(path).read()
            assert "title: Test Page" in content
            assert "# Hello" in content
        finally:
            os.unlink(path)

    def test_export_html(self):
        from wiki_cli.core.export import export_page_html

        page = {
            "title": "Test Page",
            "render": "<p>Hello World</p>",
            "description": "A test",
            "locale": "en",
        }
        client = self._mock_client(page)
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
            path = f.name
        try:
            result = export_page_html(client, 1, path, overwrite=True)
            assert result["status"] == "ok"
            assert result["format"] == "html"
            content = open(path).read()
            assert "<!DOCTYPE html>" in content
            assert "<p>Hello World</p>" in content
        finally:
            os.unlink(path)

    def test_export_json(self):
        from wiki_cli.core.export import export_page_json

        page = {
            "id": 1,
            "title": "Test Page",
            "content": "Hello",
            "path": "test",
        }
        client = self._mock_client(page)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            result = export_page_json(client, 1, path, overwrite=True)
            assert result["status"] == "ok"
            data = json.load(open(path))
            assert data["title"] == "Test Page"
        finally:
            os.unlink(path)

    def test_export_no_overwrite(self):
        from wiki_cli.core.export import export_page_markdown

        page = {
            "title": "Test",
            "content": "x",
            "description": "",
            "path": "t",
            "locale": "en",
            "tags": [],
            "editor": "markdown",
        }
        client = self._mock_client(page)
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
            path = f.name
            f.write(b"existing")
        try:
            with pytest.raises(RuntimeError, match="already exists"):
                export_page_markdown(client, 1, path, overwrite=False)
        finally:
            os.unlink(path)


# ── CLI Tests ────────────────────────────────────────────────────────


class TestCLI:
    """Tests for CLI entry point."""

    def test_help(self):
        from click.testing import CliRunner
        from wiki_cli.wiki_cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "Wiki.js" in result.output or "wiki" in result.output.lower()

    def test_version(self):
        from click.testing import CliRunner
        from wiki_cli.wiki_cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output

    def test_page_group_help(self):
        from click.testing import CliRunner
        from wiki_cli.wiki_cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["page", "--help"])
        assert result.exit_code == 0
        assert "list" in result.output
        assert "create" in result.output

    def test_all_groups_registered(self):
        from wiki_cli.wiki_cli import cli

        group_names = [cmd for cmd in cli.commands]
        for expected in [
            "page",
            "user",
            "group",
            "asset",
            "comment",
            "site",
            "export",
            "session",
            "connect",
            "repl",
        ]:
            assert expected in group_names, f"Missing command group: {expected}"
