"""Page management for Wiki.js.

Handles page CRUD, search, history, move, and render operations
via the Wiki.js GraphQL API.
"""

from typing import Optional


# ── Queries ──────────────────────────────────────────────────────────

Q_PAGE_LIST = """
query PageList($limit: Int, $orderBy: PageOrderBy, $orderByDirection: PageOrderByDirection, $tags: [String!], $locale: String) {
    pages {
        list(limit: $limit, orderBy: $orderBy, orderByDirection: $orderByDirection, tags: $tags, locale: $locale) {
            id path locale title description contentType isPublished isPrivate
            createdAt updatedAt tags
        }
    }
}
"""

Q_PAGE_SINGLE = """
query PageSingle($id: Int!) {
    pages {
        single(id: $id) {
            id path hash title description isPrivate isPublished
            content render toc contentType createdAt updatedAt
            editor locale scriptCss scriptJs
            authorId authorName authorEmail
            creatorId creatorName creatorEmail
            tags
        }
    }
}
"""

Q_PAGE_BY_PATH = """
query PageByPath($path: String!, $locale: String!) {
    pages {
        singleByPath(path: $path, locale: $locale) {
            id path hash title description isPrivate isPublished
            content render toc contentType createdAt updatedAt
            editor locale tags
            authorId authorName authorEmail
        }
    }
}
"""

Q_PAGE_SEARCH = """
query PageSearch($query: String!, $path: String, $locale: String) {
    pages {
        search(query: $query, path: $path, locale: $locale) {
            results { id title description path locale }
            suggestions
            totalHits
        }
    }
}
"""

Q_PAGE_HISTORY = """
query PageHistory($id: Int!, $offsetPage: Int, $offsetSize: Int) {
    pages {
        history(id: $id, offsetPage: $offsetPage, offsetSize: $offsetSize) {
            trail {
                versionId versionDate authorId authorName actionType
                valueBefore valueAfter
            }
            total
        }
    }
}
"""

Q_PAGE_VERSION = """
query PageVersion($pageId: Int!, $versionId: Int!) {
    pages {
        version(pageId: $pageId, versionId: $versionId) {
            action authorId authorName content contentType
            createdAt versionDate description editor isPrivate isPublished
            locale pageId path tags title versionId
        }
    }
}
"""

Q_PAGE_TREE = """
query PageTree($path: String, $parent: Int, $mode: PageTreeMode!, $locale: String!, $includeAncestors: Boolean) {
    pages {
        tree(path: $path, parent: $parent, mode: $mode, locale: $locale, includeAncestors: $includeAncestors) {
            id path depth title isPrivate isFolder parent pageId locale
        }
    }
}
"""

Q_PAGE_TAGS = """
{
    pages {
        tags { id tag title createdAt updatedAt }
    }
}
"""

# ── Mutations ────────────────────────────────────────────────────────

M_PAGE_CREATE = """
mutation PageCreate(
    $content: String!, $description: String!, $editor: String!,
    $isPublished: Boolean!, $isPrivate: Boolean!, $locale: String!,
    $path: String!, $tags: [String]!, $title: String!,
    $publishStartDate: Date, $publishEndDate: Date,
    $scriptCss: String, $scriptJs: String
) {
    pages {
        create(
            content: $content, description: $description, editor: $editor,
            isPublished: $isPublished, isPrivate: $isPrivate, locale: $locale,
            path: $path, tags: $tags, title: $title,
            publishStartDate: $publishStartDate, publishEndDate: $publishEndDate,
            scriptCss: $scriptCss, scriptJs: $scriptJs
        ) {
            responseResult { succeeded errorCode slug message }
            page { id path title }
        }
    }
}
"""

M_PAGE_UPDATE = """
mutation PageUpdate(
    $id: Int!, $content: String, $description: String,
    $editor: String, $isPrivate: Boolean, $isPublished: Boolean,
    $locale: String, $path: String, $tags: [String], $title: String,
    $scriptCss: String, $scriptJs: String
) {
    pages {
        update(
            id: $id, content: $content, description: $description,
            editor: $editor, isPrivate: $isPrivate, isPublished: $isPublished,
            locale: $locale, path: $path, tags: $tags, title: $title,
            scriptCss: $scriptCss, scriptJs: $scriptJs
        ) {
            responseResult { succeeded errorCode slug message }
            page { id path title updatedAt }
        }
    }
}
"""

M_PAGE_DELETE = """
mutation PageDelete($id: Int!) {
    pages {
        delete(id: $id) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""

M_PAGE_MOVE = """
mutation PageMove($id: Int!, $destinationPath: String!, $destinationLocale: String!) {
    pages {
        move(id: $id, destinationPath: $destinationPath, destinationLocale: $destinationLocale) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""

M_PAGE_RENDER = """
mutation PageRender($id: Int!) {
    pages {
        render(id: $id) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""

M_PAGE_RESTORE = """
mutation PageRestore($pageId: Int!, $versionId: Int!) {
    pages {
        restore(pageId: $pageId, versionId: $versionId) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""


# ── Functions ────────────────────────────────────────────────────────


def list_pages(
    client,
    limit: int = 50,
    order_by: str = "UPDATED",
    direction: str = "DESC",
    tags: Optional[list] = None,
    locale: Optional[str] = None,
) -> list:
    """List pages with optional filtering."""
    variables = {
        "limit": limit,
        "orderBy": order_by,
        "orderByDirection": direction,
    }
    if tags:
        variables["tags"] = tags
    if locale:
        variables["locale"] = locale

    data = client.execute(Q_PAGE_LIST, variables)
    return data.get("pages", {}).get("list", [])


def get_page(client, page_id: int) -> dict:
    """Get a single page by ID."""
    data = client.execute(Q_PAGE_SINGLE, {"id": page_id})
    page = data.get("pages", {}).get("single", None)
    if not page:
        raise RuntimeError(f"Page {page_id} not found")
    return page


def get_page_by_path(client, path: str, locale: str = "en") -> dict:
    """Get a page by its path and locale."""
    data = client.execute(Q_PAGE_BY_PATH, {"path": path, "locale": locale})
    page = data.get("pages", {}).get("singleByPath", None)
    if not page:
        raise RuntimeError(f"Page not found at path '{path}' (locale: {locale})")
    return page


def search_pages(
    client, query: str, path: Optional[str] = None, locale: Optional[str] = None
) -> dict:
    """Search for pages."""
    variables = {"query": query}
    if path:
        variables["path"] = path
    if locale:
        variables["locale"] = locale

    data = client.execute(Q_PAGE_SEARCH, variables)
    return data.get("pages", {}).get("search", {})


def get_page_history(
    client, page_id: int, offset_page: int = 0, offset_size: int = 25
) -> dict:
    """Get page edit history."""
    data = client.execute(
        Q_PAGE_HISTORY,
        {
            "id": page_id,
            "offsetPage": offset_page,
            "offsetSize": offset_size,
        },
    )
    return data.get("pages", {}).get("history", {})


def get_page_version(client, page_id: int, version_id: int) -> dict:
    """Get a specific version of a page."""
    data = client.execute(
        Q_PAGE_VERSION,
        {
            "pageId": page_id,
            "versionId": version_id,
        },
    )
    return data.get("pages", {}).get("version", {})


def get_page_tree(
    client,
    locale: str = "en",
    mode: str = "ALL",
    path: Optional[str] = None,
    parent: Optional[int] = None,
    include_ancestors: bool = False,
) -> list:
    """Get the page tree structure."""
    variables = {"mode": mode, "locale": locale}
    if path is not None:
        variables["path"] = path
    if parent is not None:
        variables["parent"] = parent
    if include_ancestors:
        variables["includeAncestors"] = True

    data = client.execute(Q_PAGE_TREE, variables)
    return data.get("pages", {}).get("tree", [])


def get_tags(client) -> list:
    """Get all page tags."""
    data = client.execute(Q_PAGE_TAGS)
    return data.get("pages", {}).get("tags", [])


def create_page(
    client,
    title: str,
    path: str,
    content: str,
    description: str = "",
    editor: str = "markdown",
    locale: str = "en",
    is_published: bool = True,
    is_private: bool = False,
    tags: Optional[list] = None,
) -> dict:
    """Create a new page."""
    variables = {
        "title": title,
        "path": path,
        "content": content,
        "description": description or title,
        "editor": editor,
        "locale": locale,
        "isPublished": is_published,
        "isPrivate": is_private,
        "tags": tags or [],
    }
    data = client.execute(M_PAGE_CREATE, variables)
    result = data.get("pages", {}).get("create", {})
    resp = result.get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to create page: {resp.get('message', 'Unknown error')}"
        )
    return result


def update_page(client, page_id: int, **kwargs) -> dict:
    """Update an existing page. Pass only fields to update."""
    variables = {"id": page_id}

    field_map = {
        "content": "content",
        "description": "description",
        "editor": "editor",
        "is_private": "isPrivate",
        "is_published": "isPublished",
        "locale": "locale",
        "path": "path",
        "tags": "tags",
        "title": "title",
        "script_css": "scriptCss",
        "script_js": "scriptJs",
    }

    for py_name, gql_name in field_map.items():
        if py_name in kwargs and kwargs[py_name] is not None:
            variables[gql_name] = kwargs[py_name]

    data = client.execute(M_PAGE_UPDATE, variables)
    result = data.get("pages", {}).get("update", {})
    resp = result.get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to update page: {resp.get('message', 'Unknown error')}"
        )
    return result


def delete_page(client, page_id: int) -> dict:
    """Delete a page."""
    data = client.execute(M_PAGE_DELETE, {"id": page_id})
    result = data.get("pages", {}).get("delete", {})
    resp = result.get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to delete page: {resp.get('message', 'Unknown error')}"
        )
    return result


def move_page(
    client, page_id: int, destination_path: str, destination_locale: str = "en"
) -> dict:
    """Move a page to a new path."""
    data = client.execute(
        M_PAGE_MOVE,
        {
            "id": page_id,
            "destinationPath": destination_path,
            "destinationLocale": destination_locale,
        },
    )
    result = data.get("pages", {}).get("move", {})
    resp = result.get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to move page: {resp.get('message', 'Unknown error')}"
        )
    return result


def render_page(client, page_id: int) -> dict:
    """Trigger re-render of a page."""
    data = client.execute(M_PAGE_RENDER, {"id": page_id})
    result = data.get("pages", {}).get("render", {})
    resp = result.get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to render page: {resp.get('message', 'Unknown error')}"
        )
    return result


def restore_page(client, page_id: int, version_id: int) -> dict:
    """Restore a page to a specific version."""
    data = client.execute(
        M_PAGE_RESTORE,
        {
            "pageId": page_id,
            "versionId": version_id,
        },
    )
    result = data.get("pages", {}).get("restore", {})
    resp = result.get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to restore page: {resp.get('message', 'Unknown error')}"
        )
    return result
