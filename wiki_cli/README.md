# wiki-cli

CLI harness for **Wiki.js** — manage pages, users, assets, and content from the terminal.

## Prerequisites

- **Python 3.10+**
- **Wiki.js** instance running and accessible via HTTP/HTTPS
- **API key** created in Wiki.js admin panel (Administration → API Access)

## Installation

```bash
pip install -e .
```

Verify installation:
```bash
wiki-cli --version
wiki-cli --help
```

## Quick Start

### 1. Connect to Wiki.js

```bash
wiki-cli connect http://localhost:3000 --api-key YOUR_API_KEY
```

Or use environment variables:
```bash
export WIKI_URL=http://localhost:3000
export WIKI_API_KEY=your-api-key
```

### 2. Basic Commands

```bash
# List pages
wiki-cli page list

# Create a page
wiki-cli page create -t "My Page" -p "docs/my-page" -c "# Hello World"

# Read page content
wiki-cli page read 42

# Search pages
wiki-cli page search "hello"

# Export a page
wiki-cli export page 42 output.md --format markdown

# Export all pages
wiki-cli export all ./backup --format markdown

# System info
wiki-cli site info

# User management
wiki-cli user list
wiki-cli user get 1
```

### 3. JSON Output (for agents)

```bash
wiki-cli --json page list
wiki-cli --json site info
wiki-cli --json export page 42 /tmp/page.md
```

### 4. Interactive REPL

```bash
wiki-cli
# Enters interactive mode with undo/redo, history, and tab completion
```

## Command Groups

| Group      | Description                                    |
|------------|------------------------------------------------|
| `page`     | Page CRUD, search, history, move, render       |
| `user`     | User management, activation, passwords         |
| `group`    | Group CRUD, permissions, user assignment       |
| `asset`    | File/image management, folders, upload         |
| `comment`  | Page comments CRUD                             |
| `site`     | Site configuration, system info, theming       |
| `export`   | Export pages (markdown, HTML, JSON), wiki dump  |
| `session`  | Session status, operation history, undo/redo   |
| `connect`  | Connect to a Wiki.js instance                  |

## Running Tests

### Unit tests (no Wiki.js needed)

```bash
python3 -m pytest wiki_cli/tests/test_core.py -v
```

### E2E tests (requires running Wiki.js)

```bash
export WIKI_URL=http://localhost:3000
export WIKI_API_KEY=your-api-key
python3 -m pytest wiki_cli/tests/test_full_e2e.py -v -s
```

### Force installed CLI for subprocess tests

```bash
WIKI_CLI_FORCE_INSTALLED=1 python3 -m pytest wiki_cli/tests/ -v -s
```

## Architecture

The CLI communicates with Wiki.js through its **GraphQL API** over HTTP.

```
wiki-cli → HTTP/GraphQL → Wiki.js Instance → Database
```

- **Backend client:** `utils/wiki_backend.py` — GraphQL client with auth
- **Core modules:** `core/page.py`, `core/user.py`, `core/group.py`, etc.
- **CLI:** `wiki_cli.py` — Click-based CLI with REPL mode
- **Session:** `core/session.py` — undo/redo and operation history
