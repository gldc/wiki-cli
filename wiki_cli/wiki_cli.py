"""wiki-cli: CLI harness for Wiki.js.

Provides a complete command-line interface to a running Wiki.js instance
via its GraphQL API. Supports both one-shot commands and an interactive REPL.
"""

import json
import sys
import shlex

import click

from wiki_cli import __version__
from wiki_cli.utils.wiki_backend import (
    WikiClient,
    load_config,
    save_config,
    validate_config,
    create_client,
)
from wiki_cli.core.session import Session


# ── Helpers ──────────────────────────────────────────────────────────


def _output(ctx, data, message: str = ""):
    """Output data as JSON or human-readable."""
    if ctx.obj.get("json_mode"):
        click.echo(json.dumps(data, indent=2, default=str))
    elif message:
        click.echo(message)


def _error(ctx, msg: str, code: int = 1):
    """Output error and exit."""
    if ctx.obj.get("json_mode"):
        click.echo(json.dumps({"status": "error", "message": msg}))
    else:
        click.echo(f"Error: {msg}", err=True)
    sys.exit(code)


def _get_client(ctx) -> WikiClient:
    """Get or create the Wiki.js client."""
    if "client" not in ctx.obj:
        try:
            ctx.obj["client"] = create_client()
        except RuntimeError as e:
            _error(ctx, str(e))
    return ctx.obj["client"]


def _get_session(ctx) -> Session:
    """Get or create the session."""
    if "session" not in ctx.obj:
        ctx.obj["session"] = Session()
    return ctx.obj["session"]


# ── Main CLI Group ───────────────────────────────────────────────────


@click.group(invoke_without_command=True)
@click.option("--json", "json_mode", is_flag=True, help="Output in JSON format")
@click.option("--url", envvar="WIKI_URL", help="Wiki.js instance URL")
@click.option("--api-key", envvar="WIKI_API_KEY", help="Wiki.js API key")
@click.version_option(__version__, prog_name="wiki-cli")
@click.pass_context
def cli(ctx, json_mode, url, api_key):
    """CLI harness for Wiki.js — manage pages, users, and content from the terminal."""
    ctx.ensure_object(dict)
    ctx.obj["json_mode"] = json_mode

    if url or api_key:
        config = load_config()
        if url:
            config["url"] = url
        if api_key:
            config["api_key"] = api_key
        try:
            ctx.obj["client"] = WikiClient(url=config["url"], api_key=config["api_key"])
        except Exception:
            pass

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


# ── Connect Command ──────────────────────────────────────────────────


@cli.command()
@click.argument("url")
@click.option("--api-key", "-k", required=True, help="Wiki.js API key")
@click.pass_context
def connect(ctx, url, api_key):
    """Connect to a Wiki.js instance and save configuration."""
    client = WikiClient(url=url, api_key=api_key)
    try:
        info = client.test_connection()
        save_config(url, api_key)
        msg = (
            f"Connected to Wiki.js {info.get('currentVersion', '?')} "
            f"at {url} ({info.get('pagesTotal', '?')} pages, "
            f"{info.get('usersTotal', '?')} users)"
        )
        _output(ctx, {"status": "ok", "info": info, "url": url}, msg)
    except RuntimeError as e:
        _error(ctx, str(e))


# ── Page Commands ────────────────────────────────────────────────────


@cli.group()
@click.pass_context
def page(ctx):
    """Page management — create, read, update, delete, search."""
    pass


@page.command("list")
@click.option("--limit", "-l", default=50, help="Max pages to return")
@click.option(
    "--order-by",
    type=click.Choice(["CREATED", "ID", "PATH", "TITLE", "UPDATED"]),
    default="UPDATED",
)
@click.option("--direction", type=click.Choice(["ASC", "DESC"]), default="DESC")
@click.option("--tags", "-t", multiple=True, help="Filter by tags")
@click.option("--locale", help="Filter by locale")
@click.pass_context
def page_list(ctx, limit, order_by, direction, tags, locale):
    """List wiki pages."""
    from wiki_cli.core.page import list_pages

    client = _get_client(ctx)
    try:
        pages = list_pages(
            client,
            limit=limit,
            order_by=order_by,
            direction=direction,
            tags=list(tags) if tags else None,
            locale=locale,
        )
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "pages": pages, "count": len(pages)})
        else:
            for p in pages:
                status = "+" if p.get("isPublished") else "-"
                click.echo(f"  [{status}] {p['id']:>5}  /{p['path']:<40}  {p['title']}")
            click.echo(f"\n  {len(pages)} pages")
    except RuntimeError as e:
        _error(ctx, str(e))


@page.command("get")
@click.argument("page_id", type=int)
@click.pass_context
def page_get(ctx, page_id):
    """Get a page by ID."""
    from wiki_cli.core.page import get_page

    client = _get_client(ctx)
    try:
        p = get_page(client, page_id)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "page": p})
        else:
            click.echo(f"  Title:       {p.get('title')}")
            click.echo(f"  Path:        /{p.get('path')}")
            click.echo(f"  ID:          {p.get('id')}")
            click.echo(f"  Editor:      {p.get('editor')}")
            click.echo(f"  Locale:      {p.get('locale')}")
            click.echo(f"  Published:   {p.get('isPublished')}")
            click.echo(f"  Private:     {p.get('isPrivate')}")
            click.echo(f"  Tags:        {', '.join(p.get('tags', []))}")
            click.echo(f"  Author:      {p.get('authorName')}")
            click.echo(f"  Created:     {p.get('createdAt')}")
            click.echo(f"  Updated:     {p.get('updatedAt')}")
            click.echo(f"  Description: {p.get('description')}")
    except RuntimeError as e:
        _error(ctx, str(e))


@page.command("read")
@click.argument("page_id", type=int)
@click.pass_context
def page_read(ctx, page_id):
    """Read a page's content (markdown/source)."""
    from wiki_cli.core.page import get_page

    client = _get_client(ctx)
    try:
        p = get_page(client, page_id)
        if ctx.obj.get("json_mode"):
            _output(
                ctx,
                {
                    "status": "ok",
                    "content": p.get("content", ""),
                    "title": p.get("title"),
                    "id": page_id,
                },
            )
        else:
            click.echo(p.get("content", ""))
    except RuntimeError as e:
        _error(ctx, str(e))


@page.command("find")
@click.argument("path")
@click.option("--locale", "-l", default="en", help="Page locale")
@click.pass_context
def page_find(ctx, path, locale):
    """Find a page by its path."""
    from wiki_cli.core.page import get_page_by_path

    client = _get_client(ctx)
    try:
        p = get_page_by_path(client, path, locale)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "page": p})
        else:
            click.echo(f"  ID: {p.get('id')}  /{p.get('path')}  {p.get('title')}")
    except RuntimeError as e:
        _error(ctx, str(e))


@page.command("search")
@click.argument("query")
@click.option("--path", "-p", help="Restrict to path prefix")
@click.option("--locale", "-l", help="Restrict to locale")
@click.pass_context
def page_search(ctx, query, path, locale):
    """Search for pages."""
    from wiki_cli.core.page import search_pages

    client = _get_client(ctx)
    try:
        result = search_pages(client, query, path=path, locale=locale)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "search": result})
        else:
            results = result.get("results", [])
            for r in results:
                click.echo(f"  {r['id']:>5}  /{r['path']:<40}  {r['title']}")
            click.echo(f"\n  {result.get('totalHits', len(results))} results")
    except RuntimeError as e:
        _error(ctx, str(e))


@page.command("create")
@click.option("--title", "-t", required=True, help="Page title")
@click.option("--path", "-p", required=True, help="Page path (e.g., docs/guide)")
@click.option("--content", "-c", default="", help="Page content (markdown)")
@click.option(
    "--content-file", "-f", type=click.Path(exists=True), help="Read content from file"
)
@click.option("--editor", default="markdown", help="Editor type")
@click.option("--locale", "-l", default="en", help="Locale")
@click.option("--published/--draft", default=True, help="Published or draft")
@click.option("--private/--public", default=False, help="Private or public")
@click.option("--tags", multiple=True, help="Tags")
@click.option("--description", "-d", default="", help="Page description")
@click.pass_context
def page_create(
    ctx,
    title,
    path,
    content,
    content_file,
    editor,
    locale,
    published,
    private,
    tags,
    description,
):
    """Create a new page."""
    from wiki_cli.core.page import create_page

    client = _get_client(ctx)

    if content_file:
        with open(content_file, "r") as f:
            content = f.read()

    try:
        result = create_page(
            client,
            title=title,
            path=path,
            content=content,
            description=description,
            editor=editor,
            locale=locale,
            is_published=published,
            is_private=private,
            tags=list(tags),
        )
        page_info = result.get("page", {})
        msg = f"  Created page: {page_info.get('id')} /{page_info.get('path')} — {page_info.get('title')}"
        _output(ctx, {"status": "ok", "page": page_info}, msg)

        session = _get_session(ctx)
        session.record(
            "page_create",
            f"Created page '{title}' at /{path}",
            undo_data={"page_id": page_info.get("id")},
            result=page_info,
        )
    except RuntimeError as e:
        _error(ctx, str(e))


@page.command("update")
@click.argument("page_id", type=int)
@click.option("--title", "-t", help="New title")
@click.option("--content", "-c", help="New content")
@click.option(
    "--content-file", "-f", type=click.Path(exists=True), help="Read content from file"
)
@click.option("--description", "-d", help="New description")
@click.option("--tags", multiple=True, help="New tags")
@click.option("--published/--draft", default=None, help="Published or draft")
@click.option("--private/--public", default=None, help="Private or public")
@click.pass_context
def page_update(
    ctx, page_id, title, content, content_file, description, tags, published, private
):
    """Update an existing page."""
    from wiki_cli.core.page import update_page, get_page

    client = _get_client(ctx)

    if content_file:
        with open(content_file, "r") as f:
            content = f.read()

    kwargs = {}
    if title is not None:
        kwargs["title"] = title
    if content is not None:
        kwargs["content"] = content
    if description is not None:
        kwargs["description"] = description
    if tags:
        kwargs["tags"] = list(tags)
    if published is not None:
        kwargs["is_published"] = published
    if private is not None:
        kwargs["is_private"] = private

    try:
        # Save old state for undo
        old_page = get_page(client, page_id)
        result = update_page(client, page_id, **kwargs)
        page_info = result.get("page", {})
        msg = f"  Updated page {page_id}"
        _output(ctx, {"status": "ok", "page": page_info}, msg)

        session = _get_session(ctx)
        session.record(
            "page_update",
            f"Updated page {page_id}",
            undo_data={"page_id": page_id, "old_state": old_page},
            result=page_info,
        )
    except RuntimeError as e:
        _error(ctx, str(e))


@page.command("delete")
@click.argument("page_id", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def page_delete(ctx, page_id, yes):
    """Delete a page."""
    from wiki_cli.core.page import delete_page, get_page

    client = _get_client(ctx)

    if not yes and not ctx.obj.get("json_mode"):
        try:
            p = get_page(client, page_id)
            if not click.confirm(f"Delete page {page_id} '{p.get('title')}'?"):
                return
        except RuntimeError:
            pass

    try:
        delete_page(client, page_id)
        _output(ctx, {"status": "ok", "deleted": page_id}, f"  Deleted page {page_id}")
    except RuntimeError as e:
        _error(ctx, str(e))


@page.command("move")
@click.argument("page_id", type=int)
@click.argument("destination_path")
@click.option("--locale", "-l", default="en", help="Destination locale")
@click.pass_context
def page_move(ctx, page_id, destination_path, locale):
    """Move a page to a new path."""
    from wiki_cli.core.page import move_page

    client = _get_client(ctx)
    try:
        move_page(client, page_id, destination_path, locale)
        _output(
            ctx,
            {"status": "ok", "page_id": page_id, "new_path": destination_path},
            f"  Moved page {page_id} to /{destination_path}",
        )
    except RuntimeError as e:
        _error(ctx, str(e))


@page.command("history")
@click.argument("page_id", type=int)
@click.option("--page", "offset_page", default=0, help="Page offset")
@click.option("--size", "offset_size", default=25, help="Page size")
@click.pass_context
def page_history(ctx, page_id, offset_page, offset_size):
    """View page edit history."""
    from wiki_cli.core.page import get_page_history

    client = _get_client(ctx)
    try:
        hist = get_page_history(client, page_id, offset_page, offset_size)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "history": hist})
        else:
            for entry in hist.get("trail", []):
                click.echo(
                    f"  v{entry['versionId']}  {entry['versionDate']}  "
                    f"{entry['authorName']}  [{entry['actionType']}]"
                )
            click.echo(f"\n  Total: {hist.get('total', 0)} versions")
    except RuntimeError as e:
        _error(ctx, str(e))


@page.command("render")
@click.argument("page_id", type=int)
@click.pass_context
def page_render(ctx, page_id):
    """Trigger re-render of a page."""
    from wiki_cli.core.page import render_page

    client = _get_client(ctx)
    try:
        render_page(client, page_id)
        _output(
            ctx, {"status": "ok", "page_id": page_id}, f"  Re-rendered page {page_id}"
        )
    except RuntimeError as e:
        _error(ctx, str(e))


@page.command("restore")
@click.argument("page_id", type=int)
@click.argument("version_id", type=int)
@click.pass_context
def page_restore(ctx, page_id, version_id):
    """Restore a page to a specific version."""
    from wiki_cli.core.page import restore_page

    client = _get_client(ctx)
    try:
        restore_page(client, page_id, version_id)
        _output(
            ctx,
            {"status": "ok", "page_id": page_id, "version_id": version_id},
            f"  Restored page {page_id} to version {version_id}",
        )
    except RuntimeError as e:
        _error(ctx, str(e))


@page.command("tree")
@click.option("--locale", "-l", default="en", help="Locale")
@click.option("--mode", type=click.Choice(["ALL", "FOLDERS", "PAGES"]), default="ALL")
@click.option("--path", "-p", help="Root path")
@click.pass_context
def page_tree(ctx, locale, mode, path):
    """View the page tree structure."""
    from wiki_cli.core.page import get_page_tree

    client = _get_client(ctx)
    try:
        tree = get_page_tree(client, locale=locale, mode=mode, path=path)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "tree": tree})
        else:
            for item in tree:
                indent = "  " * (item.get("depth", 0) + 1)
                icon = "📁" if item.get("isFolder") else "📄"
                click.echo(f"{indent}{icon} {item.get('title', item.get('path', '?'))}")
    except RuntimeError as e:
        _error(ctx, str(e))


@page.command("tags")
@click.pass_context
def page_tags(ctx):
    """List all page tags."""
    from wiki_cli.core.page import get_tags

    client = _get_client(ctx)
    try:
        tags = get_tags(client)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "tags": tags})
        else:
            for t in tags:
                click.echo(f"  {t['id']:>4}  {t['tag']:<30}  {t.get('title', '')}")
    except RuntimeError as e:
        _error(ctx, str(e))


# ── User Commands ────────────────────────────────────────────────────


@cli.group()
@click.pass_context
def user(ctx):
    """User management — list, create, update, delete users."""
    pass


@user.command("list")
@click.option("--filter", "-f", "filter_str", help="Filter string")
@click.option("--order-by", help="Order by field")
@click.pass_context
def user_list(ctx, filter_str, order_by):
    """List all users."""
    from wiki_cli.core.user import list_users

    client = _get_client(ctx)
    try:
        users = list_users(client, filter_str=filter_str, order_by=order_by)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "users": users, "count": len(users)})
        else:
            for u in users:
                active = "✓" if u.get("isActive") else "✗"
                click.echo(f"  [{active}] {u['id']:>5}  {u['name']:<30}  {u['email']}")
            click.echo(f"\n  {len(users)} users")
    except RuntimeError as e:
        _error(ctx, str(e))


@user.command("get")
@click.argument("user_id", type=int)
@click.pass_context
def user_get(ctx, user_id):
    """Get user details."""
    from wiki_cli.core.user import get_user

    client = _get_client(ctx)
    try:
        u = get_user(client, user_id)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "user": u})
        else:
            click.echo(f"  Name:     {u.get('name')}")
            click.echo(f"  Email:    {u.get('email')}")
            click.echo(f"  ID:       {u.get('id')}")
            click.echo(f"  Active:   {u.get('isActive')}")
            click.echo(f"  Verified: {u.get('isVerified')}")
            click.echo(f"  Provider: {u.get('providerName')}")
            click.echo(
                f"  Groups:   {', '.join(g['name'] for g in u.get('groups', []))}"
            )
            click.echo(f"  Created:  {u.get('createdAt')}")
    except RuntimeError as e:
        _error(ctx, str(e))


@user.command("search")
@click.argument("query")
@click.pass_context
def user_search(ctx, query):
    """Search for users."""
    from wiki_cli.core.user import search_users

    client = _get_client(ctx)
    try:
        users = search_users(client, query)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "users": users})
        else:
            for u in users:
                click.echo(f"  {u['id']:>5}  {u['name']:<30}  {u['email']}")
    except RuntimeError as e:
        _error(ctx, str(e))


@user.command("create")
@click.option("--email", "-e", required=True, help="Email address")
@click.option("--name", "-n", required=True, help="Display name")
@click.option("--password", "-p", help="Password (for local auth)")
@click.option("--groups", "-g", multiple=True, type=int, help="Group IDs")
@click.pass_context
def user_create(ctx, email, name, password, groups):
    """Create a new user."""
    from wiki_cli.core.user import create_user

    client = _get_client(ctx)
    try:
        result = create_user(
            client,
            email=email,
            name=name,
            password=password,
            groups=list(groups) if groups else None,
        )
        user_info = result.get("user", {})
        _output(
            ctx,
            {"status": "ok", "user": user_info},
            f"  Created user: {user_info.get('id')} {user_info.get('name')}",
        )
    except RuntimeError as e:
        _error(ctx, str(e))


@user.command("update")
@click.argument("user_id", type=int)
@click.option("--name", "-n", help="New name")
@click.option("--email", "-e", help="New email")
@click.option("--password", help="New password")
@click.pass_context
def user_update(ctx, user_id, name, email, password):
    """Update a user."""
    from wiki_cli.core.user import update_user

    client = _get_client(ctx)
    kwargs = {}
    if name:
        kwargs["name"] = name
    if email:
        kwargs["email"] = email
    if password:
        kwargs["new_password"] = password
    try:
        update_user(client, user_id, **kwargs)
        _output(ctx, {"status": "ok", "user_id": user_id}, f"  Updated user {user_id}")
    except RuntimeError as e:
        _error(ctx, str(e))


@user.command("delete")
@click.argument("user_id", type=int)
@click.option("--replace-id", default=1, help="User ID to reassign content to")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def user_delete(ctx, user_id, replace_id, yes):
    """Delete a user."""
    from wiki_cli.core.user import delete_user

    client = _get_client(ctx)
    if not yes and not ctx.obj.get("json_mode"):
        if not click.confirm(f"Delete user {user_id}?"):
            return
    try:
        delete_user(client, user_id, replace_id)
        _output(ctx, {"status": "ok", "deleted": user_id}, f"  Deleted user {user_id}")
    except RuntimeError as e:
        _error(ctx, str(e))


@user.command("activate")
@click.argument("user_id", type=int)
@click.pass_context
def user_activate(ctx, user_id):
    """Activate a user."""
    from wiki_cli.core.user import activate_user

    client = _get_client(ctx)
    try:
        activate_user(client, user_id)
        _output(
            ctx, {"status": "ok", "user_id": user_id}, f"  Activated user {user_id}"
        )
    except RuntimeError as e:
        _error(ctx, str(e))


@user.command("deactivate")
@click.argument("user_id", type=int)
@click.pass_context
def user_deactivate(ctx, user_id):
    """Deactivate a user."""
    from wiki_cli.core.user import deactivate_user

    client = _get_client(ctx)
    try:
        deactivate_user(client, user_id)
        _output(
            ctx, {"status": "ok", "user_id": user_id}, f"  Deactivated user {user_id}"
        )
    except RuntimeError as e:
        _error(ctx, str(e))


@user.command("profile")
@click.pass_context
def user_profile(ctx):
    """View current user profile."""
    from wiki_cli.core.user import get_profile

    client = _get_client(ctx)
    try:
        profile = get_profile(client)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "profile": profile})
        else:
            click.echo(f"  Name:     {profile.get('name')}")
            click.echo(f"  Email:    {profile.get('email')}")
            click.echo(f"  Pages:    {profile.get('pagesTotal')}")
            click.echo(
                f"  Groups:   {', '.join(g['name'] for g in profile.get('groups', []))}"
            )
    except RuntimeError as e:
        _error(ctx, str(e))


# ── Group Commands ───────────────────────────────────────────────────


@cli.group("group")
@click.pass_context
def group_cmd(ctx):
    """Group management — create, update, delete, assign users."""
    pass


@group_cmd.command("list")
@click.pass_context
def group_list(ctx):
    """List all groups."""
    from wiki_cli.core.group import list_groups

    client = _get_client(ctx)
    try:
        groups = list_groups(client)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "groups": groups})
        else:
            for g in groups:
                sys_tag = " [system]" if g.get("isSystem") else ""
                click.echo(
                    f"  {g['id']:>4}  {g['name']:<30}  {g.get('userCount', 0)} users{sys_tag}"
                )
    except RuntimeError as e:
        _error(ctx, str(e))


@group_cmd.command("get")
@click.argument("group_id", type=int)
@click.pass_context
def group_get(ctx, group_id):
    """Get group details."""
    from wiki_cli.core.group import get_group

    client = _get_client(ctx)
    try:
        g = get_group(client, group_id)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "group": g})
        else:
            click.echo(f"  Name:        {g.get('name')}")
            click.echo(f"  ID:          {g.get('id')}")
            click.echo(f"  System:      {g.get('isSystem')}")
            click.echo(f"  Permissions: {len(g.get('permissions', []))}")
            click.echo(f"  Page Rules:  {len(g.get('pageRules', []))}")
            click.echo(f"  Users:       {len(g.get('users', []))}")
    except RuntimeError as e:
        _error(ctx, str(e))


@group_cmd.command("create")
@click.option("--name", "-n", required=True, help="Group name")
@click.pass_context
def group_create(ctx, name):
    """Create a new group."""
    from wiki_cli.core.group import create_group

    client = _get_client(ctx)
    try:
        result = create_group(client, name)
        group_info = result.get("group", {})
        _output(
            ctx,
            {"status": "ok", "group": group_info},
            f"  Created group: {group_info.get('id')} {group_info.get('name')}",
        )
    except RuntimeError as e:
        _error(ctx, str(e))


@group_cmd.command("delete")
@click.argument("group_id", type=int)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
@click.pass_context
def group_delete(ctx, group_id, yes):
    """Delete a group."""
    from wiki_cli.core.group import delete_group

    client = _get_client(ctx)
    if not yes and not ctx.obj.get("json_mode"):
        if not click.confirm(f"Delete group {group_id}?"):
            return
    try:
        delete_group(client, group_id)
        _output(
            ctx, {"status": "ok", "deleted": group_id}, f"  Deleted group {group_id}"
        )
    except RuntimeError as e:
        _error(ctx, str(e))


@group_cmd.command("assign-user")
@click.argument("group_id", type=int)
@click.argument("user_id", type=int)
@click.pass_context
def group_assign_user(ctx, group_id, user_id):
    """Assign a user to a group."""
    from wiki_cli.core.group import assign_user

    client = _get_client(ctx)
    try:
        assign_user(client, group_id, user_id)
        _output(
            ctx,
            {"status": "ok", "group_id": group_id, "user_id": user_id},
            f"  Assigned user {user_id} to group {group_id}",
        )
    except RuntimeError as e:
        _error(ctx, str(e))


@group_cmd.command("unassign-user")
@click.argument("group_id", type=int)
@click.argument("user_id", type=int)
@click.pass_context
def group_unassign_user(ctx, group_id, user_id):
    """Remove a user from a group."""
    from wiki_cli.core.group import unassign_user

    client = _get_client(ctx)
    try:
        unassign_user(client, group_id, user_id)
        _output(
            ctx,
            {"status": "ok", "group_id": group_id, "user_id": user_id},
            f"  Removed user {user_id} from group {group_id}",
        )
    except RuntimeError as e:
        _error(ctx, str(e))


# ── Asset Commands ───────────────────────────────────────────────────


@cli.group()
@click.pass_context
def asset(ctx):
    """Asset management — files, images, folders."""
    pass


@asset.command("list")
@click.option("--folder-id", "-f", default=0, help="Folder ID (0 for root)")
@click.option("--kind", type=click.Choice(["ALL", "IMAGE", "BINARY"]), default="ALL")
@click.pass_context
def asset_list(ctx, folder_id, kind):
    """List assets in a folder."""
    from wiki_cli.core.asset import list_assets

    client = _get_client(ctx)
    try:
        assets = list_assets(client, folder_id=folder_id, kind=kind)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "assets": assets})
        else:
            for a in assets:
                size = a.get("fileSize", 0)
                click.echo(
                    f"  {a['id']:>5}  {a['filename']:<40}  {size:>10,} bytes  {a.get('ext', '')}"
                )
            click.echo(f"\n  {len(assets)} assets")
    except RuntimeError as e:
        _error(ctx, str(e))


@asset.command("folders")
@click.option("--parent-id", "-p", default=0, help="Parent folder ID")
@click.pass_context
def asset_folders(ctx, parent_id):
    """List asset folders."""
    from wiki_cli.core.asset import list_folders

    client = _get_client(ctx)
    try:
        folders = list_folders(client, parent_folder_id=parent_id)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "folders": folders})
        else:
            for f in folders:
                click.echo(f"  📁 {f['id']:>4}  {f['slug']:<20}  {f.get('name', '')}")
    except RuntimeError as e:
        _error(ctx, str(e))


@asset.command("upload")
@click.argument("file_path", type=click.Path(exists=True))
@click.option("--folder-id", "-f", default=0, help="Target folder ID")
@click.pass_context
def asset_upload(ctx, file_path, folder_id):
    """Upload a file."""
    from wiki_cli.core.asset import upload_asset

    client = _get_client(ctx)
    try:
        result = upload_asset(client, file_path, folder_id=folder_id)
        _output(ctx, result, f"  Uploaded: {result.get('filename')}")
    except RuntimeError as e:
        _error(ctx, str(e))


@asset.command("delete")
@click.argument("asset_id", type=int)
@click.option("--yes", "-y", is_flag=True)
@click.pass_context
def asset_delete(ctx, asset_id, yes):
    """Delete an asset."""
    from wiki_cli.core.asset import delete_asset

    client = _get_client(ctx)
    if not yes and not ctx.obj.get("json_mode"):
        if not click.confirm(f"Delete asset {asset_id}?"):
            return
    try:
        delete_asset(client, asset_id)
        _output(
            ctx, {"status": "ok", "deleted": asset_id}, f"  Deleted asset {asset_id}"
        )
    except RuntimeError as e:
        _error(ctx, str(e))


# ── Comment Commands ─────────────────────────────────────────────────


@cli.group()
@click.pass_context
def comment(ctx):
    """Comment management on pages."""
    pass


@comment.command("list")
@click.argument("page_path")
@click.option("--locale", "-l", default="en")
@click.pass_context
def comment_list(ctx, page_path, locale):
    """List comments on a page."""
    from wiki_cli.core.comment import list_comments

    client = _get_client(ctx)
    try:
        comments = list_comments(client, path=page_path, locale=locale)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "comments": comments})
        else:
            for c in comments:
                click.echo(
                    f"  #{c['id']}  {c.get('authorName', '?')}  {c.get('createdAt', '')}"
                )
                click.echo(f"    {c.get('content', '')[:100]}")
    except RuntimeError as e:
        _error(ctx, str(e))


@comment.command("create")
@click.argument("page_id", type=int)
@click.option("--content", "-c", required=True, help="Comment content")
@click.option("--reply-to", type=int, help="Reply to comment ID")
@click.pass_context
def comment_create(ctx, page_id, content, reply_to):
    """Add a comment to a page."""
    from wiki_cli.core.comment import create_comment

    client = _get_client(ctx)
    try:
        result = create_comment(client, page_id, content, reply_to=reply_to)
        _output(
            ctx,
            {"status": "ok", "id": result.get("id")},
            f"  Created comment #{result.get('id')}",
        )
    except RuntimeError as e:
        _error(ctx, str(e))


@comment.command("delete")
@click.argument("comment_id", type=int)
@click.option("--yes", "-y", is_flag=True)
@click.pass_context
def comment_delete(ctx, comment_id, yes):
    """Delete a comment."""
    from wiki_cli.core.comment import delete_comment

    client = _get_client(ctx)
    if not yes and not ctx.obj.get("json_mode"):
        if not click.confirm(f"Delete comment {comment_id}?"):
            return
    try:
        delete_comment(client, comment_id)
        _output(
            ctx,
            {"status": "ok", "deleted": comment_id},
            f"  Deleted comment {comment_id}",
        )
    except RuntimeError as e:
        _error(ctx, str(e))


# ── Site/System Commands ─────────────────────────────────────────────


@cli.group()
@click.pass_context
def site(ctx):
    """Site configuration and system info."""
    pass


@site.command("config")
@click.pass_context
def site_config(ctx):
    """View site configuration."""
    from wiki_cli.core.site import get_site_config

    client = _get_client(ctx)
    try:
        config = get_site_config(client)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "config": config})
        else:
            click.echo(f"  Host:     {config.get('host')}")
            click.echo(f"  Title:    {config.get('title')}")
            click.echo(f"  Company:  {config.get('company')}")
            click.echo(f"  License:  {config.get('contentLicense')}")
            click.echo(f"  Ratings:  {config.get('featurePageRatings')}")
            click.echo(f"  Comments: {config.get('featurePageComments')}")
    except RuntimeError as e:
        _error(ctx, str(e))


@site.command("info")
@click.pass_context
def site_info(ctx):
    """View system information."""
    from wiki_cli.core.site import get_system_info

    client = _get_client(ctx)
    try:
        info = get_system_info(client)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "info": info})
        else:
            click.echo(f"  Version:  {info.get('currentVersion')}")
            click.echo(f"  Latest:   {info.get('latestVersion')}")
            click.echo(f"  Host:     {info.get('hostname')}")
            click.echo(f"  OS:       {info.get('operatingSystem')}")
            click.echo(f"  Node:     {info.get('nodeVersion')}")
            click.echo(f"  DB:       {info.get('dbType')} @ {info.get('dbHost')}")
            click.echo(f"  Pages:    {info.get('pagesTotal')}")
            click.echo(f"  Users:    {info.get('usersTotal')}")
            click.echo(f"  Groups:   {info.get('groupsTotal')}")
            click.echo(f"  Tags:     {info.get('tagsTotal')}")
    except RuntimeError as e:
        _error(ctx, str(e))


@site.command("theming")
@click.pass_context
def site_theming(ctx):
    """View theming configuration."""
    from wiki_cli.core.site import get_theming

    client = _get_client(ctx)
    try:
        theming = get_theming(client)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "theming": theming})
        else:
            config = theming.get("config", {})
            click.echo(f"  Theme:    {config.get('theme')}")
            click.echo(f"  Iconset:  {config.get('iconset')}")
            click.echo(f"  Dark:     {config.get('darkMode')}")
    except RuntimeError as e:
        _error(ctx, str(e))


@site.command("locales")
@click.pass_context
def site_locales(ctx):
    """View locale configuration."""
    from wiki_cli.core.site import get_locales

    client = _get_client(ctx)
    try:
        loc = get_locales(client)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "localization": loc})
        else:
            config = loc.get("config", {})
            click.echo(f"  Active locale: {config.get('locale')}")
            installed = [l for l in loc.get("locales", []) if l.get("isInstalled")]
            for l in installed:
                click.echo(
                    f"    {l['code']:<6}  {l['name']:<20}  {l.get('nativeName', '')}"
                )
    except RuntimeError as e:
        _error(ctx, str(e))


@site.command("nav")
@click.pass_context
def site_nav(ctx):
    """View navigation tree."""
    from wiki_cli.core.site import get_nav_tree

    client = _get_client(ctx)
    try:
        tree = get_nav_tree(client)
        if ctx.obj.get("json_mode"):
            _output(ctx, {"status": "ok", "navigation": tree})
        else:
            for locale_tree in tree:
                click.echo(f"  [{locale_tree.get('locale')}]")
                for item in locale_tree.get("items", []):
                    click.echo(f"    {item.get('icon', '•')} {item.get('label')}")
    except RuntimeError as e:
        _error(ctx, str(e))


# ── Export Commands ──────────────────────────────────────────────────


@cli.group("export")
@click.pass_context
def export_cmd(ctx):
    """Export pages and wiki content."""
    pass


@export_cmd.command("page")
@click.argument("page_id", type=int)
@click.argument("output_path")
@click.option(
    "--format",
    "-f",
    "fmt",
    type=click.Choice(["markdown", "html", "json"]),
    default="markdown",
    help="Export format",
)
@click.option("--overwrite", is_flag=True, help="Overwrite existing file")
@click.pass_context
def export_page(ctx, page_id, output_path, fmt, overwrite):
    """Export a single page."""
    from wiki_cli.core.export import (
        export_page_markdown,
        export_page_html,
        export_page_json,
    )

    client = _get_client(ctx)
    export_fns = {
        "markdown": export_page_markdown,
        "html": export_page_html,
        "json": export_page_json,
    }
    try:
        result = export_fns[fmt](client, page_id, output_path, overwrite=overwrite)
        if ctx.obj.get("json_mode"):
            _output(ctx, result)
        else:
            click.echo(
                f"  Exported: {result['output']} ({result['file_size']:,} bytes)"
            )
    except RuntimeError as e:
        _error(ctx, str(e))


@export_cmd.command("all")
@click.argument("output_dir")
@click.option(
    "--format",
    "-f",
    "fmt",
    type=click.Choice(["markdown", "html", "json"]),
    default="markdown",
)
@click.option("--locale", "-l", help="Filter by locale")
@click.option("--overwrite", is_flag=True)
@click.pass_context
def export_all(ctx, output_dir, fmt, locale, overwrite):
    """Export all pages to a directory."""
    from wiki_cli.core.export import export_all_pages

    client = _get_client(ctx)
    try:
        result = export_all_pages(
            client, output_dir, fmt=fmt, locale=locale, overwrite=overwrite
        )
        if ctx.obj.get("json_mode"):
            _output(ctx, result)
        else:
            click.echo(f"  Exported {result['exported_count']} pages to {output_dir}")
            if result["error_count"]:
                click.echo(f"  Errors: {result['error_count']}")
    except RuntimeError as e:
        _error(ctx, str(e))


@export_cmd.command("server")
@click.option(
    "--entities",
    "-e",
    multiple=True,
    default=["pages", "users", "groups", "settings"],
    help="Entities to export",
)
@click.option("--path", "-p", required=True, help="Server-side export path")
@click.pass_context
def export_server(ctx, entities, path):
    """Trigger server-side wiki export."""
    from wiki_cli.core.export import export_wiki_server

    client = _get_client(ctx)
    try:
        export_wiki_server(client, list(entities), path)
        _output(
            ctx,
            {"status": "ok", "entities": list(entities), "path": path},
            f"  Server export started to {path}",
        )
    except RuntimeError as e:
        _error(ctx, str(e))


# ── Session Commands ─────────────────────────────────────────────────


@cli.group()
@click.pass_context
def session(ctx):
    """Session management — status, history, undo/redo."""
    pass


@session.command("status")
@click.pass_context
def session_status(ctx):
    """Show session status."""
    s = _get_session(ctx)
    status = s.status()
    if ctx.obj.get("json_mode"):
        _output(ctx, {"status": "ok", "session": status})
    else:
        click.echo(f"  URL:          {status.get('url') or '(from config)'}")
        click.echo(f"  Page context: {status.get('current_page_path') or 'none'}")
        click.echo(f"  Locale:       {status.get('current_locale')}")
        click.echo(f"  History:      {status.get('history_count')} operations")
        click.echo(f"  Redo stack:   {status.get('redo_count')}")


@session.command("history")
@click.option("--limit", "-l", default=20, help="Max entries")
@click.pass_context
def session_history(ctx, limit):
    """Show operation history."""
    s = _get_session(ctx)
    history = s.history(limit)
    if ctx.obj.get("json_mode"):
        _output(ctx, {"status": "ok", "history": [op.to_dict() for op in history]})
    else:
        for op in history:
            import time as _time

            ts = _time.strftime("%H:%M:%S", _time.localtime(op.timestamp))
            click.echo(f"  [{ts}] {op.op_type}: {op.description}")
        if not history:
            click.echo("  No operations recorded")


# ── REPL ─────────────────────────────────────────────────────────────


@cli.command()
@click.argument("project_path", required=False)
@click.pass_context
def repl(ctx, project_path):
    """Start interactive REPL session."""
    from wiki_cli.utils.repl_skin import ReplSkin

    skin = ReplSkin("wiki", version=__version__)
    skin.print_banner()

    # Try to connect
    try:
        config = load_config()
        if config.get("url") and config.get("api_key"):
            client = WikiClient(url=config["url"], api_key=config["api_key"])
            info = client.test_connection()
            ctx.obj["client"] = client
            skin.success(
                f"Connected to Wiki.js {info.get('currentVersion', '?')} "
                f"({info.get('pagesTotal', '?')} pages)"
            )
        else:
            skin.warning("Not connected. Use: connect <url> --api-key <key>")
    except Exception as e:
        skin.warning(f"Not connected: {e}")

    session = _get_session(ctx)
    pt_session = skin.create_prompt_session()

    commands_help = {
        "connect <url> -k <key>": "Connect to Wiki.js",
        "page list": "List pages",
        "page get <id>": "Get page details",
        "page read <id>": "Read page content",
        "page create -t <title> -p <path>": "Create page",
        "page search <query>": "Search pages",
        "user list": "List users",
        "group list": "List groups",
        "asset list": "List assets",
        "site info": "System information",
        "export page <id> <path>": "Export page",
        "export all <dir>": "Export all pages",
        "session status": "Session status",
        "session history": "Operation history",
        "help": "Show commands",
        "quit / exit": "Exit REPL",
    }

    while True:
        try:
            context = ""
            if "client" in ctx.obj:
                context = (
                    config.get("url", "")
                    .replace("http://", "")
                    .replace("https://", "")[:30]
                )
            line = skin.get_input(
                pt_session, context=context, modified=session.modified
            )
        except (EOFError, KeyboardInterrupt):
            skin.print_goodbye()
            break

        if not line:
            continue

        cmd = line.strip().lower()
        if cmd in ("quit", "exit", "q"):
            skin.print_goodbye()
            break
        if cmd == "help":
            skin.help(commands_help)
            continue
        if cmd == "undo":
            op = session.undo()
            if op:
                skin.success(f"Undone: {op.description}")
            else:
                skin.warning("Nothing to undo")
            continue
        if cmd == "redo":
            op = session.redo()
            if op:
                skin.success(f"Redone: {op.description}")
            else:
                skin.warning("Nothing to redo")
            continue

        # Parse and dispatch to Click commands
        try:
            args = shlex.split(line)
        except ValueError as e:
            skin.error(f"Parse error: {e}")
            continue

        try:
            with cli.make_context(
                "wiki-cli", list(args), parent=ctx, resilient_parsing=False
            ) as sub_ctx:
                sub_ctx.obj = ctx.obj
                cli.invoke(sub_ctx)
        except click.exceptions.UsageError as e:
            skin.error(str(e))
        except SystemExit:
            pass
        except Exception as e:
            skin.error(str(e))


# ── Entry point ──────────────────────────────────────────────────────


def main():
    cli(obj={})


if __name__ == "__main__":
    main()
