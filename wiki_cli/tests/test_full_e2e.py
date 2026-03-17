"""E2E tests for wiki-cli.

These tests require a running Wiki.js instance.
Set WIKI_URL and WIKI_API_KEY environment variables.

CLI subprocess tests use _resolve_cli() to find the installed command.
"""

import json
import os
import subprocess
import sys
import tempfile

import pytest


# ── Helpers ──────────────────────────────────────────────────────────


def _resolve_cli(name):
    """Resolve installed CLI command; falls back to python -m for dev.

    Set env WIKI_CLI_FORCE_INSTALLED=1 to require the installed command.
    """
    import shutil

    force = os.environ.get("WIKI_CLI_FORCE_INSTALLED", "").strip() == "1"
    path = shutil.which(name)
    if path:
        print(f"[_resolve_cli] Using installed command: {path}")
        return [path]
    if force:
        raise RuntimeError(f"{name} not found in PATH. Install with: pip install -e .")
    module = "wiki_cli.wiki_cli"
    print(f"[_resolve_cli] Falling back to: {sys.executable} -m {module}")
    return [sys.executable, "-m", module]


def _wiki_configured():
    """Check if Wiki.js is configured via environment."""
    return bool(os.environ.get("WIKI_URL") and os.environ.get("WIKI_API_KEY"))


skip_no_wiki = pytest.mark.skipif(
    not _wiki_configured(),
    reason="WIKI_URL and WIKI_API_KEY not set — no Wiki.js instance available",
)


# ── E2E Tests with Real Wiki.js ─────────────────────────────────────


@skip_no_wiki
class TestWikiE2E:
    """E2E tests that communicate with a real Wiki.js instance."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        from wiki_cli.utils.wiki_backend import WikiClient

        self.client = WikiClient(
            url=os.environ["WIKI_URL"],
            api_key=os.environ["WIKI_API_KEY"],
        )

    def test_connection(self):
        info = self.client.test_connection()
        assert "currentVersion" in info
        assert info["pagesTotal"] is not None
        print(
            f"\n  Wiki.js {info['currentVersion']} — "
            f"{info['pagesTotal']} pages, {info['usersTotal']} users"
        )

    def test_system_info(self):
        from wiki_cli.core.site import get_system_info

        info = get_system_info(self.client)
        assert info["currentVersion"]
        assert info["dbType"]

    def test_page_lifecycle(self):
        """Full page lifecycle: create → get → update → search → export → delete."""
        from wiki_cli.core.page import (
            create_page,
            get_page,
            update_page,
            search_pages,
            delete_page,
        )
        from wiki_cli.core.export import export_page_markdown

        # Create
        result = create_page(
            self.client,
            title="CLI Test Page",
            path="wiki-cli-test-page",
            content="# Test\nThis is a test page created by wiki-cli.",
            description="E2E test page",
            tags=["test", "wiki-cli"],
        )
        page_id = result["page"]["id"]
        print(f"\n  Created page: {page_id}")

        try:
            # Get
            page = get_page(self.client, page_id)
            assert page["title"] == "CLI Test Page"
            assert page["path"] == "wiki-cli-test-page"

            # Update
            update_page(
                self.client,
                page_id,
                content="# Updated\nThis page was updated by wiki-cli.",
                tags=["test", "wiki-cli", "updated"],
            )
            updated = get_page(self.client, page_id)
            assert "Updated" in updated["content"]

            # Search
            results = search_pages(self.client, "CLI Test Page")
            assert (
                results.get("totalHits", 0) > 0 or len(results.get("results", [])) > 0
            )

            # Export
            with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
                export_path = f.name
            try:
                export_result = export_page_markdown(
                    self.client, page_id, export_path, overwrite=True
                )
                assert os.path.exists(export_path)
                assert export_result["file_size"] > 0
                content = open(export_path).read()
                assert "title: CLI Test Page" in content or "Updated" in content
                print(
                    f"  Exported: {export_path} ({export_result['file_size']:,} bytes)"
                )
            finally:
                os.unlink(export_path)

        finally:
            # Cleanup: delete the test page
            delete_page(self.client, page_id)
            print(f"  Deleted page: {page_id}")

    def test_list_pages(self):
        from wiki_cli.core.page import list_pages

        pages = list_pages(self.client, limit=10)
        assert isinstance(pages, list)
        print(f"\n  Listed {len(pages)} pages")

    def test_list_users(self):
        from wiki_cli.core.user import list_users

        users = list_users(self.client)
        assert isinstance(users, list)
        assert len(users) > 0  # At least admin user
        print(f"\n  Listed {len(users)} users")

    def test_list_groups(self):
        from wiki_cli.core.group import list_groups

        groups = list_groups(self.client)
        assert isinstance(groups, list)
        assert len(groups) > 0  # At least default groups
        print(f"\n  Listed {len(groups)} groups")

    def test_site_config(self):
        from wiki_cli.core.site import get_site_config

        config = get_site_config(self.client)
        assert "title" in config
        print(f"\n  Site: {config.get('title')}")

    def test_tags(self):
        from wiki_cli.core.page import get_tags

        tags = get_tags(self.client)
        assert isinstance(tags, list)

    def test_page_tree(self):
        from wiki_cli.core.page import get_page_tree

        tree = get_page_tree(self.client, locale="en", mode="ALL")
        assert isinstance(tree, list)

    def test_export_page_html(self):
        """Create a page, export as HTML, verify output."""
        from wiki_cli.core.page import create_page, delete_page
        from wiki_cli.core.export import export_page_html

        result = create_page(
            self.client,
            title="HTML Export Test",
            path="wiki-cli-html-test",
            content="<p>HTML test content</p>",
            editor="markdown",
        )
        page_id = result["page"]["id"]

        try:
            with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
                html_path = f.name
            try:
                export_result = export_page_html(
                    self.client, page_id, html_path, overwrite=True
                )
                assert os.path.exists(html_path)
                content = open(html_path).read()
                assert "<!DOCTYPE html>" in content
                assert "HTML Export Test" in content
                print(f"\n  HTML: {html_path} ({export_result['file_size']:,} bytes)")
            finally:
                os.unlink(html_path)
        finally:
            delete_page(self.client, page_id)


# ── CLI Subprocess Tests ─────────────────────────────────────────────


class TestCLISubprocess:
    """Test the installed CLI command via subprocess."""

    CLI_BASE = _resolve_cli("wiki-cli")

    def _run(self, args, check=True):
        return subprocess.run(
            self.CLI_BASE + args,
            capture_output=True,
            text=True,
            check=check,
        )

    def test_help(self):
        result = self._run(["--help"])
        assert result.returncode == 0
        assert "page" in result.stdout
        assert "user" in result.stdout

    def test_version(self):
        result = self._run(["--version"])
        assert result.returncode == 0
        assert "1.0.0" in result.stdout

    @skip_no_wiki
    def test_json_site_info(self):
        result = self._run(["--json", "site", "info"], check=False)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            assert data["status"] == "ok"
            assert "info" in data

    @skip_no_wiki
    def test_json_page_list(self):
        result = self._run(["--json", "page", "list"], check=False)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            assert data["status"] == "ok"
            assert "pages" in data

    @skip_no_wiki
    def test_full_workflow(self):
        """Full workflow via subprocess: create → read → export → delete."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create page
            result = self._run(
                [
                    "--json",
                    "page",
                    "create",
                    "-t",
                    "Subprocess Test",
                    "-p",
                    "wiki-cli-subprocess-test",
                    "-c",
                    "# Subprocess Test\nCreated via subprocess.",
                ],
                check=False,
            )
            if result.returncode != 0:
                pytest.skip(f"Cannot create page: {result.stderr}")

            data = json.loads(result.stdout)
            page_id = str(data["page"]["id"])

            try:
                # Read page
                result = self._run(["--json", "page", "get", page_id])
                assert result.returncode == 0
                page_data = json.loads(result.stdout)
                assert page_data["page"]["title"] == "Subprocess Test"

                # Export page
                export_path = os.path.join(tmp_dir, "test.md")
                result = self._run(
                    [
                        "export",
                        "page",
                        page_id,
                        export_path,
                        "--format",
                        "markdown",
                        "--overwrite",
                    ]
                )
                assert result.returncode == 0
                assert os.path.exists(export_path)
                content = open(export_path).read()
                assert "Subprocess Test" in content
                print(
                    f"\n  Exported: {export_path} ({os.path.getsize(export_path):,} bytes)"
                )

            finally:
                # Delete page
                self._run(["page", "delete", page_id, "-y"], check=False)
