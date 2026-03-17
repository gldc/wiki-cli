"""Group management for Wiki.js."""

from typing import Optional


Q_GROUP_LIST = """
query GroupList($filter: String, $orderBy: String) {
    groups {
        list(filter: $filter, orderBy: $orderBy) {
            id name isSystem userCount createdAt updatedAt
        }
    }
}
"""

Q_GROUP_SINGLE = """
query GroupSingle($id: Int!) {
    groups {
        single(id: $id) {
            id name isSystem redirectOnLogin permissions
            pageRules { id deny match roles path locales }
            users { id name email }
            createdAt updatedAt
        }
    }
}
"""

M_GROUP_CREATE = """
mutation GroupCreate($name: String!) {
    groups {
        create(name: $name) {
            responseResult { succeeded errorCode slug message }
            group { id name }
        }
    }
}
"""

M_GROUP_UPDATE = """
mutation GroupUpdate(
    $id: Int!, $name: String!, $redirectOnLogin: String!,
    $permissions: [String]!, $pageRules: [PageRuleInput]!
) {
    groups {
        update(
            id: $id, name: $name, redirectOnLogin: $redirectOnLogin,
            permissions: $permissions, pageRules: $pageRules
        ) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""

M_GROUP_DELETE = """
mutation GroupDelete($id: Int!) {
    groups {
        delete(id: $id) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""

M_GROUP_ASSIGN_USER = """
mutation GroupAssignUser($groupId: Int!, $userId: Int!) {
    groups {
        assignUser(groupId: $groupId, userId: $userId) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""

M_GROUP_UNASSIGN_USER = """
mutation GroupUnassignUser($groupId: Int!, $userId: Int!) {
    groups {
        unassignUser(groupId: $groupId, userId: $userId) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""


def list_groups(
    client, filter_str: Optional[str] = None, order_by: Optional[str] = None
) -> list:
    variables = {}
    if filter_str:
        variables["filter"] = filter_str
    if order_by:
        variables["orderBy"] = order_by
    data = client.execute(Q_GROUP_LIST, variables)
    return data.get("groups", {}).get("list", [])


def get_group(client, group_id: int) -> dict:
    data = client.execute(Q_GROUP_SINGLE, {"id": group_id})
    group = data.get("groups", {}).get("single", None)
    if not group:
        raise RuntimeError(f"Group {group_id} not found")
    return group


def create_group(client, name: str) -> dict:
    data = client.execute(M_GROUP_CREATE, {"name": name})
    result = data.get("groups", {}).get("create", {})
    resp = result.get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to create group: {resp.get('message', 'Unknown error')}"
        )
    return result


def update_group(
    client,
    group_id: int,
    name: str,
    redirect_on_login: str = "/",
    permissions: Optional[list] = None,
    page_rules: Optional[list] = None,
) -> dict:
    variables = {
        "id": group_id,
        "name": name,
        "redirectOnLogin": redirect_on_login,
        "permissions": permissions or [],
        "pageRules": page_rules or [],
    }
    data = client.execute(M_GROUP_UPDATE, variables)
    resp = data.get("groups", {}).get("update", {}).get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to update group: {resp.get('message', 'Unknown error')}"
        )
    return resp


def delete_group(client, group_id: int) -> dict:
    data = client.execute(M_GROUP_DELETE, {"id": group_id})
    resp = data.get("groups", {}).get("delete", {}).get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to delete group: {resp.get('message', 'Unknown error')}"
        )
    return resp


def assign_user(client, group_id: int, user_id: int) -> dict:
    data = client.execute(
        M_GROUP_ASSIGN_USER,
        {
            "groupId": group_id,
            "userId": user_id,
        },
    )
    resp = data.get("groups", {}).get("assignUser", {}).get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to assign user: {resp.get('message', 'Unknown error')}"
        )
    return resp


def unassign_user(client, group_id: int, user_id: int) -> dict:
    data = client.execute(
        M_GROUP_UNASSIGN_USER,
        {
            "groupId": group_id,
            "userId": user_id,
        },
    )
    resp = data.get("groups", {}).get("unassignUser", {}).get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to unassign user: {resp.get('message', 'Unknown error')}"
        )
    return resp
