---
name: "wiki-cli"
description: "Command-line interface for Wiki.js — manage pages, users, assets, and content via the GraphQL API"
---

# wiki-cli

CLI harness for Wiki.js. Provides complete command-line access to a Wiki.js instance via its GraphQL API. Supports page management, user administration, asset handling, content export, and interactive REPL sessions.

## Installation

This CLI is installed as part of the wiki-cli package:

```bash
pip install wiki-cli
```

**Prerequisites:**
- Python 3.10+
- Wiki.js instance running and accessible via HTTP/HTTPS
- API key created via Wiki.js admin panel (Administration → API Access)

## Usage

### Basic Commands

```bash
# Show help
wiki-cli --help

# Start interactive REPL mode
wiki-cli

# Connect to Wiki.js instance
wiki-cli connect http://localhost:3000 --api-key YOUR_KEY

# Run with JSON output (for agent consumption)
wiki-cli --json page list
```

## Command Groups

### Page
Page management — create, read, update, delete, search, move, history, render, restore.

| Command | Description |
|---------|-------------|
| `list` | List wiki pages with filtering and sorting |
| `get` | Get full page details by ID |
| `read` | Read page source content |
| `find` | Find a page by its path |
| `search` | Full-text search across pages |
| `create` | Create a new page |
| `update` | Update an existing page |
| `delete` | Delete a page |
| `move` | Move a page to a new path |
| `history` | View page edit history |
| `render` | Trigger page re-render |
| `restore` | Restore page to a specific version |
| `tree` | View page tree structure |
| `tags` | List all page tags |

### User
User management — list, create, update, delete, activate/deactivate.

| Command | Description |
|---------|-------------|
| `list` | List all users |
| `get` | Get user details |
| `search` | Search for users |
| `create` | Create a new user |
| `update` | Update a user |
| `delete` | Delete a user |
| `activate` | Activate a user |
| `deactivate` | Deactivate a user |
| `profile` | View current user profile |

### Group
Group management — CRUD, permissions, user assignment.

| Command | Description |
|---------|-------------|
| `list` | List all groups |
| `get` | Get group details with permissions |
| `create` | Create a new group |
| `delete` | Delete a group |
| `assign-user` | Add a user to a group |
| `unassign-user` | Remove a user from a group |

### Asset
File and image management.

| Command | Description |
|---------|-------------|
| `list` | List assets in a folder |
| `folders` | List asset folders |
| `upload` | Upload a file |
| `delete` | Delete an asset |

### Comment
Page comment management.

| Command | Description |
|---------|-------------|
| `list` | List comments on a page |
| `create` | Add a comment |
| `delete` | Delete a comment |

### Site
Site configuration and system information.

| Command | Description |
|---------|-------------|
| `config` | View site configuration |
| `info` | View system information |
| `theming` | View theme settings |
| `locales` | View locale configuration |
| `nav` | View navigation tree |

### Export
Export pages and wiki content.

| Command | Description |
|---------|-------------|
| `page` | Export a single page (markdown, HTML, or JSON) |
| `all` | Export all pages to a directory |
| `server` | Trigger server-side wiki export |

### Session
Session management with undo/redo.

| Command | Description |
|---------|-------------|
| `status` | Show session status |
| `history` | Show operation history |

## Examples

### Create a New Page
```bash
wiki-cli page create -t "Getting Started" -p "docs/getting-started" \
  -c "# Getting Started\nWelcome to the wiki." -d "Introduction guide"

# Or with JSON output for programmatic use
wiki-cli --json page create -t "API Guide" -p "docs/api" -c "# API\nEndpoints..."
```

### Export All Pages as Backup
```bash
wiki-cli export all ./wiki-backup --format markdown --overwrite
```

### Interactive REPL Session
```bash
wiki-cli
# Enter commands interactively
# Use 'help' to see available commands
# Use 'undo' and 'redo' for history navigation
```

### Content from File
```bash
wiki-cli page create -t "Release Notes" -p "releases/v2" \
  --content-file ./RELEASE_NOTES.md
```

## For AI Agents

When using this CLI programmatically:

1. **Always use `--json` flag** for parseable output
2. **Check return codes** — 0 for success, non-zero for errors
3. **Parse stderr** for error messages on failure
4. **Use absolute paths** for all file operations
5. **Verify outputs exist** after export operations
6. **Set environment variables** for connection: `WIKI_URL`, `WIKI_API_KEY`

## Version

1.0.0
