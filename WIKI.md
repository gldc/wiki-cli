# Wiki.js — wiki-cli SOP

## Software Overview

**Wiki.js** is a modern, lightweight, and powerful wiki application built on Node.js, Git, and Markdown.
- **Version:** 2.0.0
- **License:** AGPLv3
- **Repository:** https://github.com/Requarks/wiki

## Architecture

### Backend Engine
- **Framework:** Express.js 4.18.2
- **API:** Apollo Server 2.25.2 (GraphQL)
- **ORM:** Objection.js 2.2.18 / Knex.js 0.21.7
- **Database:** PostgreSQL (recommended), MySQL, SQLite, MS SQL
- **Auth:** Passport.js with 20+ strategies

### Frontend
- **Framework:** Vue.js 2.6.14 with Vuetify 2.3.15
- **State:** Vuex 3.5.1
- **API Client:** Apollo Client 2.6.10

### Data Model
- Pages (content, metadata, history, versions)
- Users (accounts, profiles, groups)
- Assets (file storage with folders)
- Tags, Comments, Navigation
- Modular: Storage (11 backends), Search (9 engines), Auth (20+ providers), Rendering (25+ engines)

## CLI Strategy

### How the CLI Uses Wiki.js

Unlike desktop GUI apps (GIMP, Blender), Wiki.js is a **web application**. The CLI communicates with a running Wiki.js instance via its **GraphQL API** over HTTP.

**The pattern:**
1. Connect to Wiki.js instance (URL + API key)
2. Execute GraphQL queries/mutations
3. Return structured results (human-readable or JSON)

**The real software dependency:** A running Wiki.js instance with API access enabled.

### GUI Action → API Mapping

| GUI Action | GraphQL Operation |
|------------|------------------|
| Create page | `pages.create` mutation |
| Edit page | `pages.update` mutation |
| Delete page | `pages.delete` mutation |
| Move page | `pages.move` mutation |
| Search | `pages.search` query |
| View history | `pages.history` query |
| Manage users | `users.*` queries/mutations |
| Upload asset | REST upload + `assets.*` |
| Configure site | `site.updateConfig` mutation |
| View system info | `system.info` query |

### Command Groups

1. **page** — Page CRUD, search, history, move, render
2. **user** — User management, activation, passwords
3. **group** — Group CRUD, permissions, user assignment
4. **asset** — File/image management, folders
5. **comment** — Page comments CRUD
6. **nav** — Navigation tree management
7. **site** — Site configuration
8. **system** — System info, export, flags
9. **auth** — Authentication, API keys
10. **session** — Connection management, undo/redo

### State Model

- **Connection state:** URL, API key, stored in `~/.wiki-cli/config.json`
- **Session state:** Current page context, undo/redo history, stored in session JSON
- **Output format:** Human-readable tables (default) or JSON (`--json` flag)

### Output Format

All commands support `--json` for machine-readable output:
```json
{
  "status": "ok",
  "data": { ... },
  "message": "Page created successfully"
}
```

## Dependencies

### Hard Dependencies
- **Wiki.js instance** — Running and accessible via HTTP/HTTPS
- **API key** — Created via Wiki.js admin panel (Administration → API Access)

### Python Dependencies
- `click>=8.0.0` — CLI framework
- `prompt-toolkit>=3.0.0` — REPL enhancements
- `requests>=2.28.0` — HTTP client for GraphQL API
