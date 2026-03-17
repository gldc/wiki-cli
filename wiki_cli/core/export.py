"""Export operations for Wiki.js.

Handles exporting pages to various formats (Markdown, HTML, raw content)
and triggering server-side wiki exports.
"""

import json
import os
from typing import Optional


def export_page_markdown(
    client, page_id: int, output_path: str, overwrite: bool = False
) -> dict:
    """Export a page's content as Markdown."""
    from wiki_cli.core.page import get_page

    if os.path.exists(output_path) and not overwrite:
        raise RuntimeError(
            f"File already exists: {output_path}. Use --overwrite to replace."
        )

    page = get_page(client, page_id)
    content = page.get("content", "")
    title = page.get("title", "Untitled")
    description = page.get("description", "")

    # Build markdown with frontmatter
    lines = [
        "---",
        f"title: {title}",
        f"description: {description}",
        f"path: {page.get('path', '')}",
        f"locale: {page.get('locale', 'en')}",
        f"tags: {json.dumps(page.get('tags', []))}",
        f"editor: {page.get('editor', 'markdown')}",
        "---",
        "",
        content,
    ]

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    file_size = os.path.getsize(output_path)
    return {
        "status": "ok",
        "output": output_path,
        "format": "markdown",
        "file_size": file_size,
        "page_id": page_id,
        "title": title,
    }


def export_page_html(
    client, page_id: int, output_path: str, overwrite: bool = False
) -> dict:
    """Export a page's rendered HTML."""
    from wiki_cli.core.page import get_page

    if os.path.exists(output_path) and not overwrite:
        raise RuntimeError(
            f"File already exists: {output_path}. Use --overwrite to replace."
        )

    page = get_page(client, page_id)
    render = page.get("render", "")
    title = page.get("title", "Untitled")

    html = f"""<!DOCTYPE html>
<html lang="{page.get("locale", "en")}">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{title}</title>
    <meta name="description" content="{page.get("description", "")}">
</head>
<body>
    <article>
        <h1>{title}</h1>
        {render}
    </article>
</body>
</html>"""

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    file_size = os.path.getsize(output_path)
    return {
        "status": "ok",
        "output": output_path,
        "format": "html",
        "file_size": file_size,
        "page_id": page_id,
        "title": title,
    }


def export_page_json(
    client, page_id: int, output_path: str, overwrite: bool = False
) -> dict:
    """Export a page as a JSON file with all metadata."""
    from wiki_cli.core.page import get_page

    if os.path.exists(output_path) and not overwrite:
        raise RuntimeError(
            f"File already exists: {output_path}. Use --overwrite to replace."
        )

    page = get_page(client, page_id)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(page, f, indent=2, ensure_ascii=False)

    file_size = os.path.getsize(output_path)
    return {
        "status": "ok",
        "output": output_path,
        "format": "json",
        "file_size": file_size,
        "page_id": page_id,
        "title": page.get("title", "Untitled"),
    }


def export_all_pages(
    client,
    output_dir: str,
    fmt: str = "markdown",
    locale: Optional[str] = None,
    overwrite: bool = False,
) -> dict:
    """Export all pages to a directory."""
    from wiki_cli.core.page import list_pages

    pages = list_pages(client, limit=9999, locale=locale)
    os.makedirs(output_dir, exist_ok=True)

    exported = []
    errors = []

    for page_info in pages:
        page_id = page_info["id"]
        page_path = page_info.get("path", str(page_id))

        # Create subdirectories matching wiki path
        safe_path = page_path.replace("/", os.sep)

        if fmt == "markdown":
            ext = ".md"
            export_fn = export_page_markdown
        elif fmt == "html":
            ext = ".html"
            export_fn = export_page_html
        else:
            ext = ".json"
            export_fn = export_page_json

        output_path = os.path.join(output_dir, safe_path + ext)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        try:
            result = export_fn(client, page_id, output_path, overwrite=overwrite)
            exported.append(result)
        except Exception as e:
            errors.append({"page_id": page_id, "path": page_path, "error": str(e)})

    return {
        "status": "ok",
        "output_dir": output_dir,
        "format": fmt,
        "exported_count": len(exported),
        "error_count": len(errors),
        "exported": exported,
        "errors": errors,
    }


def export_wiki_server(client, entities: list, path: str) -> dict:
    """Trigger a server-side wiki export.

    This uses Wiki.js's built-in export functionality.
    Entities can include: 'users', 'groups', 'settings', 'pages', etc.
    Path is the server-side path where the export will be saved.
    """
    from wiki_cli.core.site import export_wiki as _export

    return _export(client, entities, path)
