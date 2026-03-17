"""User management for Wiki.js."""

from typing import Optional


Q_USER_LIST = """
query UserList($filter: String, $orderBy: String) {
    users {
        list(filter: $filter, orderBy: $orderBy) {
            id name email providerKey isSystem isActive createdAt lastLoginAt
        }
    }
}
"""

Q_USER_SINGLE = """
query UserSingle($id: Int!) {
    users {
        single(id: $id) {
            id name email providerKey providerName isSystem isActive isVerified
            location jobTitle timezone dateFormat appearance
            createdAt updatedAt lastLoginAt tfaIsActive
            groups { id name }
        }
    }
}
"""

Q_USER_SEARCH = """
query UserSearch($query: String!) {
    users {
        search(query: $query) {
            id name email providerKey isSystem isActive createdAt lastLoginAt
        }
    }
}
"""

Q_USER_PROFILE = """
{
    users {
        profile {
            id name email providerKey providerName isSystem isVerified
            location jobTitle timezone dateFormat appearance
            createdAt updatedAt lastLoginAt
            groups { id name }
            pagesTotal
        }
    }
}
"""

M_USER_CREATE = """
mutation UserCreate(
    $email: String!, $name: String!, $passwordRaw: String,
    $providerKey: String!, $groups: [Int]!,
    $mustChangePassword: Boolean, $sendWelcomeEmail: Boolean
) {
    users {
        create(
            email: $email, name: $name, passwordRaw: $passwordRaw,
            providerKey: $providerKey, groups: $groups,
            mustChangePassword: $mustChangePassword,
            sendWelcomeEmail: $sendWelcomeEmail
        ) {
            responseResult { succeeded errorCode slug message }
            user { id name email }
        }
    }
}
"""

M_USER_UPDATE = """
mutation UserUpdate(
    $id: Int!, $email: String, $name: String, $newPassword: String,
    $groups: [Int], $location: String, $jobTitle: String,
    $timezone: String, $dateFormat: String, $appearance: String
) {
    users {
        update(
            id: $id, email: $email, name: $name, newPassword: $newPassword,
            groups: $groups, location: $location, jobTitle: $jobTitle,
            timezone: $timezone, dateFormat: $dateFormat, appearance: $appearance
        ) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""

M_USER_DELETE = """
mutation UserDelete($id: Int!, $replaceId: Int!) {
    users {
        delete(id: $id, replaceId: $replaceId) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""

M_USER_ACTIVATE = """
mutation UserActivate($id: Int!) {
    users {
        activate(id: $id) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""

M_USER_DEACTIVATE = """
mutation UserDeactivate($id: Int!) {
    users {
        deactivate(id: $id) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""

M_USER_VERIFY = """
mutation UserVerify($id: Int!) {
    users {
        verify(id: $id) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""


def list_users(
    client, filter_str: Optional[str] = None, order_by: Optional[str] = None
) -> list:
    variables = {}
    if filter_str:
        variables["filter"] = filter_str
    if order_by:
        variables["orderBy"] = order_by
    data = client.execute(Q_USER_LIST, variables)
    return data.get("users", {}).get("list", [])


def get_user(client, user_id: int) -> dict:
    data = client.execute(Q_USER_SINGLE, {"id": user_id})
    user = data.get("users", {}).get("single", None)
    if not user:
        raise RuntimeError(f"User {user_id} not found")
    return user


def search_users(client, query: str) -> list:
    data = client.execute(Q_USER_SEARCH, {"query": query})
    return data.get("users", {}).get("search", [])


def get_profile(client) -> dict:
    data = client.execute(Q_USER_PROFILE)
    return data.get("users", {}).get("profile", {})


def create_user(
    client,
    email: str,
    name: str,
    password: Optional[str] = None,
    provider_key: str = "local",
    groups: Optional[list] = None,
    must_change_password: bool = False,
    send_welcome_email: bool = False,
) -> dict:
    variables = {
        "email": email,
        "name": name,
        "providerKey": provider_key,
        "groups": groups or [1],
    }
    if password:
        variables["passwordRaw"] = password
    if must_change_password:
        variables["mustChangePassword"] = True
    if send_welcome_email:
        variables["sendWelcomeEmail"] = True

    data = client.execute(M_USER_CREATE, variables)
    result = data.get("users", {}).get("create", {})
    resp = result.get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to create user: {resp.get('message', 'Unknown error')}"
        )
    return result


def update_user(client, user_id: int, **kwargs) -> dict:
    variables = {"id": user_id}
    field_map = {
        "email": "email",
        "name": "name",
        "new_password": "newPassword",
        "groups": "groups",
        "location": "location",
        "job_title": "jobTitle",
        "timezone": "timezone",
        "date_format": "dateFormat",
        "appearance": "appearance",
    }
    for py_name, gql_name in field_map.items():
        if py_name in kwargs and kwargs[py_name] is not None:
            variables[gql_name] = kwargs[py_name]

    data = client.execute(M_USER_UPDATE, variables)
    result = data.get("users", {}).get("update", {})
    resp = result.get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to update user: {resp.get('message', 'Unknown error')}"
        )
    return result


def delete_user(client, user_id: int, replace_id: int = 1) -> dict:
    data = client.execute(M_USER_DELETE, {"id": user_id, "replaceId": replace_id})
    result = data.get("users", {}).get("delete", {})
    resp = result.get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to delete user: {resp.get('message', 'Unknown error')}"
        )
    return result


def activate_user(client, user_id: int) -> dict:
    data = client.execute(M_USER_ACTIVATE, {"id": user_id})
    resp = data.get("users", {}).get("activate", {}).get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(f"Failed to activate user: {resp.get('message')}")
    return resp


def deactivate_user(client, user_id: int) -> dict:
    data = client.execute(M_USER_DEACTIVATE, {"id": user_id})
    resp = data.get("users", {}).get("deactivate", {}).get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(f"Failed to deactivate user: {resp.get('message')}")
    return resp


def verify_user(client, user_id: int) -> dict:
    data = client.execute(M_USER_VERIFY, {"id": user_id})
    resp = data.get("users", {}).get("verify", {}).get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(f"Failed to verify user: {resp.get('message')}")
    return resp
