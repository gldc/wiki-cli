# wiki-cli

CLI for [Wiki.js](https://js.wiki) — manage pages, users, assets, and content from the terminal via the GraphQL API.

```
wiki-cli → HTTP/GraphQL → Wiki.js Instance → Database
```

## Installation

```bash
pip install -e .
```

Requires **Python 3.10+** and a running **Wiki.js** instance with [API access enabled](https://docs.requarks.io/dev/api).

## Quick Start

```bash
# Connect to your Wiki.js instance
wiki-cli connect http://localhost:3000 --api-key YOUR_API_KEY

# Or use environment variables
export WIKI_URL=http://localhost:3000
export WIKI_API_KEY=your-api-key
```

```bash
# List pages
wiki-cli page list

# Create a page
wiki-cli page create -t "My Page" -p "docs/my-page" -c "# Hello World"

# Search
wiki-cli page search "hello"

# Export a page as markdown
wiki-cli export page 42 output.md

# Export all pages
wiki-cli export all ./backup --format markdown

# System info
wiki-cli site info
```

## JSON Output

All commands support `--json` for programmatic use:

```bash
wiki-cli --json page list
wiki-cli --json site info
```

## Interactive REPL

Running `wiki-cli` with no arguments starts an interactive session with command history, auto-suggest, and undo/redo:

```bash
wiki-cli
```

## Commands

| Group     | Description                                   |
|-----------|-----------------------------------------------|
| `page`    | Page CRUD, search, history, move, render      |
| `user`    | User management, activation, passwords        |
| `group`   | Group CRUD, permissions, user assignment      |
| `asset`   | File/image management, folders, upload        |
| `comment` | Page comments CRUD                            |
| `site`    | Site configuration, system info, theming      |
| `export`  | Export pages (markdown, HTML, JSON)            |
| `session` | Session status, operation history, undo/redo  |
| `connect` | Connect to a Wiki.js instance                 |

Run `wiki-cli <group> --help` for details on any command group.

## Tests

```bash
# Unit tests (no Wiki.js needed)
python3 -m pytest wiki_cli/tests/test_core.py -v

# E2E tests (requires running Wiki.js)
WIKI_URL=http://localhost:3000 WIKI_API_KEY=your-key \
  python3 -m pytest wiki_cli/tests/test_full_e2e.py -v -s
```

## License

MIT
