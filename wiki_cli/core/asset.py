"""Asset management for Wiki.js."""

from typing import Optional


Q_ASSET_LIST = """
query AssetList($folderId: Int!, $kind: AssetKind!) {
    assets {
        list(folderId: $folderId, kind: $kind) {
            id filename ext kind mime fileSize metadata createdAt updatedAt
            folder { id slug name }
            author { id name }
        }
    }
}
"""

Q_ASSET_FOLDERS = """
query AssetFolders($parentFolderId: Int!) {
    assets {
        folders(parentFolderId: $parentFolderId) {
            id slug name
        }
    }
}
"""

M_ASSET_CREATE_FOLDER = """
mutation AssetCreateFolder($parentFolderId: Int!, $slug: String!, $name: String) {
    assets {
        createFolder(parentFolderId: $parentFolderId, slug: $slug, name: $name) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""

M_ASSET_RENAME = """
mutation AssetRename($id: Int!, $filename: String!) {
    assets {
        renameAsset(id: $id, filename: $filename) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""

M_ASSET_DELETE = """
mutation AssetDelete($id: Int!) {
    assets {
        deleteAsset(id: $id) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""

M_ASSET_FLUSH_TEMP = """
mutation {
    assets {
        flushTempUploads {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""


def list_assets(client, folder_id: int = 0, kind: str = "ALL") -> list:
    data = client.execute(Q_ASSET_LIST, {"folderId": folder_id, "kind": kind})
    return data.get("assets", {}).get("list", [])


def list_folders(client, parent_folder_id: int = 0) -> list:
    data = client.execute(Q_ASSET_FOLDERS, {"parentFolderId": parent_folder_id})
    return data.get("assets", {}).get("folders", [])


def create_folder(
    client, slug: str, parent_folder_id: int = 0, name: Optional[str] = None
) -> dict:
    variables = {
        "parentFolderId": parent_folder_id,
        "slug": slug,
    }
    if name:
        variables["name"] = name

    data = client.execute(M_ASSET_CREATE_FOLDER, variables)
    resp = data.get("assets", {}).get("createFolder", {}).get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to create folder: {resp.get('message', 'Unknown error')}"
        )
    return resp


def rename_asset(client, asset_id: int, filename: str) -> dict:
    data = client.execute(M_ASSET_RENAME, {"id": asset_id, "filename": filename})
    resp = data.get("assets", {}).get("renameAsset", {}).get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to rename asset: {resp.get('message', 'Unknown error')}"
        )
    return resp


def delete_asset(client, asset_id: int) -> dict:
    data = client.execute(M_ASSET_DELETE, {"id": asset_id})
    resp = data.get("assets", {}).get("deleteAsset", {}).get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to delete asset: {resp.get('message', 'Unknown error')}"
        )
    return resp


def flush_temp_uploads(client) -> dict:
    data = client.execute(M_ASSET_FLUSH_TEMP)
    resp = data.get("assets", {}).get("flushTempUploads", {}).get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to flush temp uploads: {resp.get('message', 'Unknown error')}"
        )
    return resp


def upload_asset(client, file_path: str, folder_id: int = 0) -> dict:
    """Upload a file asset via REST endpoint.

    Wiki.js uses a REST endpoint for file uploads, not GraphQL.
    POST /u with multipart form data.
    """
    import os
    import requests

    if not os.path.exists(file_path):
        raise RuntimeError(f"File not found: {file_path}")

    filename = os.path.basename(file_path)
    upload_url = f"{client.url}/u"

    with open(file_path, "rb") as f:
        files = {"mediaUpload": (filename, f)}
        data = {"mediaUpload": "", "folderId": str(folder_id)}
        headers = {"Authorization": f"Bearer {client.api_key}"}

        resp = requests.post(
            upload_url, files=files, data=data, headers=headers, timeout=client.timeout
        )

    if resp.status_code != 200:
        raise RuntimeError(
            f"Upload failed with HTTP {resp.status_code}: {resp.text[:200]}"
        )

    result = resp.json()
    if not result.get("ok"):
        raise RuntimeError(f"Upload failed: {result.get('message', 'Unknown error')}")

    return {
        "status": "ok",
        "filename": filename,
        "message": "File uploaded successfully",
    }
