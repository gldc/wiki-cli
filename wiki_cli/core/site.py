"""Site configuration and system operations for Wiki.js."""

from typing import Optional


Q_SITE_CONFIG = """
{
    site {
        config {
            host title description robots analyticsService analyticsId
            company contentLicense footerOverride logoUrl pageExtensions
            authAutoLogin authEnforce2FA authHideLocal authLoginBgUrl
            authJwtAudience authJwtExpiration authJwtRenewablePeriod
            editFab editMenuBar editMenuBtn editMenuExternalBtn
            editMenuExternalName editMenuExternalIcon editMenuExternalUrl
            featurePageRatings featurePageComments featurePersonalWikis
            securityOpenRedirect securityIframe securityReferrerPolicy
            securityTrustProxy securitySRI securityHSTS securityHSTSDuration
            securityCSP securityCSPDirectives
            uploadMaxFileSize uploadMaxFiles uploadScanSVG uploadForceDownload
        }
    }
}
"""

Q_SYSTEM_INFO = """
{
    system {
        info {
            configFile cpuCores currentVersion dbHost dbType dbVersion
            groupsTotal hostname httpPort httpRedirection httpsPort
            latestVersion latestVersionReleaseDate nodeVersion
            operatingSystem pagesTotal platform ramTotal
            sslDomain sslExpirationDate sslProvider sslStatus
            sslSubscriberEmail tagsTotal telemetry telemetryClientId
            upgradeCapable usersTotal workingDirectory
        }
    }
}
"""

Q_SYSTEM_FLAGS = """
{
    system {
        flags { key value }
    }
}
"""

Q_SYSTEM_EXPORT_STATUS = """
{
    system {
        exportStatus { status progress message startedAt }
    }
}
"""

M_SITE_UPDATE_CONFIG = """
mutation SiteUpdateConfig(
    $host: String, $title: String, $description: String,
    $company: String, $contentLicense: String,
    $featurePageRatings: Boolean, $featurePageComments: Boolean,
    $uploadMaxFileSize: Int, $uploadMaxFiles: Int
) {
    site {
        updateConfig(
            host: $host, title: $title, description: $description,
            company: $company, contentLicense: $contentLicense,
            featurePageRatings: $featurePageRatings,
            featurePageComments: $featurePageComments,
            uploadMaxFileSize: $uploadMaxFileSize,
            uploadMaxFiles: $uploadMaxFiles
        ) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""

M_SYSTEM_EXPORT = """
mutation SystemExport($entities: [String]!, $path: String!) {
    system {
        export(entities: $entities, path: $path) {
            responseResult { succeeded errorCode slug message }
        }
    }
}
"""

Q_NAV_TREE = """
{
    navigation {
        tree {
            locale
            items {
                id kind label icon targetType target visibilityMode visibilityGroups
            }
        }
    }
}
"""

Q_NAV_CONFIG = """
{
    navigation {
        config { mode }
    }
}
"""

Q_THEMING_CONFIG = """
{
    theming {
        config { theme iconset darkMode tocPosition injectCSS injectHead injectBody }
        themes { key title author }
    }
}
"""

Q_LOCALES = """
{
    localization {
        locales {
            availability code createdAt installDate isInstalled isRTL name nativeName updatedAt
        }
        config { locale autoUpdate namespacing namespaces }
    }
}
"""


def get_site_config(client) -> dict:
    data = client.execute(Q_SITE_CONFIG)
    return data.get("site", {}).get("config", {})


def get_system_info(client) -> dict:
    data = client.execute(Q_SYSTEM_INFO)
    return data.get("system", {}).get("info", {})


def get_system_flags(client) -> list:
    data = client.execute(Q_SYSTEM_FLAGS)
    return data.get("system", {}).get("flags", [])


def get_export_status(client) -> dict:
    data = client.execute(Q_SYSTEM_EXPORT_STATUS)
    return data.get("system", {}).get("exportStatus", {})


def update_site_config(client, **kwargs) -> dict:
    field_map = {
        "host": "host",
        "title": "title",
        "description": "description",
        "company": "company",
        "content_license": "contentLicense",
        "feature_page_ratings": "featurePageRatings",
        "feature_page_comments": "featurePageComments",
        "upload_max_file_size": "uploadMaxFileSize",
        "upload_max_files": "uploadMaxFiles",
    }
    variables = {}
    for py_name, gql_name in field_map.items():
        if py_name in kwargs and kwargs[py_name] is not None:
            variables[gql_name] = kwargs[py_name]

    data = client.execute(M_SITE_UPDATE_CONFIG, variables)
    resp = data.get("site", {}).get("updateConfig", {}).get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to update site config: {resp.get('message', 'Unknown error')}"
        )
    return resp


def export_wiki(client, entities: list, path: str) -> dict:
    data = client.execute(M_SYSTEM_EXPORT, {"entities": entities, "path": path})
    resp = data.get("system", {}).get("export", {}).get("responseResult", {})
    if not resp.get("succeeded"):
        raise RuntimeError(
            f"Failed to start export: {resp.get('message', 'Unknown error')}"
        )
    return resp


def get_nav_tree(client) -> list:
    data = client.execute(Q_NAV_TREE)
    return data.get("navigation", {}).get("tree", [])


def get_nav_config(client) -> dict:
    data = client.execute(Q_NAV_CONFIG)
    return data.get("navigation", {}).get("config", {})


def get_theming(client) -> dict:
    data = client.execute(Q_THEMING_CONFIG)
    return data.get("theming", {})


def get_locales(client) -> dict:
    data = client.execute(Q_LOCALES)
    return data.get("localization", {})
