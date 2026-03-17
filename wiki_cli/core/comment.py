"""Comment management for Wiki.js."""

from typing import Optional


Q_COMMENT_LIST = """
query CommentList($locale: String!, $path: String!) {
    comments {
        list(locale: $locale, path: $path) {
            id content render authorId authorName authorEmail authorIP
            createdAt updatedAt
        }
    }
}
"""

Q_COMMENT_SINGLE = """
query CommentSingle($id: Int!) {
    comments {
        single(id: $id) {
            id content render authorId authorName authorEmail authorIP
            createdAt updatedAt
        }
    }
}
"""

M_COMMENT_CREATE = """
mutation CommentCreate($pageId: Int!, $content: String!, $replyTo: Int, $guestName: String, $guestEmail: String) {
    comments {
        create(pageId: $pageId, content: $content, replyTo: $replyTo, guestName: $guestName, guestEmail: $guestEmail) {
            responseResult { succeeded errorCode slug message }
            id
        }
    }
}
"""

M_COMMENT_UPDATE = """
mutation CommentUpdate($id: Int!, $content: String!) {
    comments {
        update(id: $id, content: $content) {
            responseResult { succeeded errorCode slug message }
            render
        }
    }
}
"""

M_COMMENT_DELETE = """
mutation CommentDelete($id: Int!) {
    comments {
        delete(id: $id) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""


def list_comments(client, path: str, locale: str = "en") -> list:
    data = client.execute(Q_COMMENT_LIST, {"locale": locale, "path": path})
    return data.get("comments", {}).get("list", [])


def get_comment(client, comment_id: int) -> dict:
    data = client.execute(Q_COMMENT_SINGLE, {"id": comment_id})
    comment = data.get("comments", {}).get("single", None)
    if not comment:
        raise RuntimeError(f"Comment {comment_id} not found")
    return comment


def create_comment(
    client,
    page_id: int,
    content: str,
    reply_to: Optional[int] = None,
    guest_name: Optional[str] = None,
    guest_email: Optional[str] = None,
) -> dict:
    variables = {"pageId": page_id, "content": content}
    if reply_to is not None:
        variables["replyTo"] = reply_to
    if guest_name:
        variables["guestName"] = guest_name
    if guest_email:
        variables["guestEmail"] = guest_email

    data = client.execute(M_COMMENT_CREATE, variables)
    result = data.get("comments", {}).get("create", {})
    resp = result.get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to create comment: {resp.get('message', 'Unknown error')}"
        )
    return result


def update_comment(client, comment_id: int, content: str) -> dict:
    data = client.execute(M_COMMENT_UPDATE, {"id": comment_id, "content": content})
    result = data.get("comments", {}).get("update", {})
    resp = result.get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to update comment: {resp.get('message', 'Unknown error')}"
        )
    return result


def delete_comment(client, comment_id: int) -> dict:
    data = client.execute(M_COMMENT_DELETE, {"id": comment_id})
    resp = data.get("comments", {}).get("delete", {}).get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to delete comment: {resp.get('message', 'Unknown error')}"
        )
    return resp
