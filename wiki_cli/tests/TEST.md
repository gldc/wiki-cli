# TEST.md — wiki-cli Test Plan and Results

## Test Inventory Plan

- `test_core.py`: ~30 unit tests (synthetic data, no network)
- `test_full_e2e.py`: ~15 E2E tests (requires running Wiki.js + subprocess CLI tests)

## Unit Test Plan (`test_core.py`)

### Session Module (`session.py`)
- Create session, verify initial state
- Record operations, verify history
- Undo operation, verify stack
- Redo operation, verify stack
- Clear history
- Save/load session to/from file
- Round-trip: save then load preserves state
- Session status dict
- History limit
- Undo with empty history returns None
- Redo with empty redo stack returns None
- **Expected: 11 tests**

### Backend Module (`wiki_backend.py`)
- Load config from file
- Load config with env var overrides
- Save and reload config
- Validate config — missing URL raises error
- Validate config — missing API key raises error
- WikiClient initialization
- WikiClient GraphQL URL construction
- **Expected: 7 tests**

### Page Module (`page.py`)
- GraphQL query string validity (no syntax errors)
- Field mapping in update_page
- **Expected: 2 tests**

### Export Module (`export.py`)
- Export markdown writes correct frontmatter
- Export HTML wraps content correctly
- Export JSON writes valid JSON
- Export refuses overwrite without flag
- **Expected: 4 tests**

### CLI Module (`wiki_cli.py`)
- CLI --help exits 0
- CLI --version exits 0
- CLI --json flag sets context
- All command groups registered
- **Expected: 4 tests**

**Total unit tests planned: ~28**

## E2E Test Plan (`test_full_e2e.py`)

### Requirements
- Running Wiki.js instance (URL + API key)
- Set `WIKI_URL` and `WIKI_API_KEY` environment variables

### Tests with Real Wiki.js
- Connect and get system info
- Create page, verify returned ID
- Get page by ID
- Update page content
- Search for page
- Export page as markdown, verify file exists
- Export page as HTML, verify valid HTML
- Delete page
- List users
- List groups
- **Expected: 10 tests**

### CLI Subprocess Tests (`TestCLISubprocess`)
- `--help` returns 0
- `--version` returns 0
- `--json site info` returns valid JSON
- `--json page list` returns valid JSON
- Full workflow: connect → create page → read → export → delete
- **Expected: 5 tests**

## Realistic Workflow Scenarios

### Documentation Migration
1. List all pages
2. Export all pages as markdown
3. Verify exported files on disk
4. Simulates: backing up a wiki to git

### Content Management Pipeline
1. Create page with markdown content from file
2. Update page tags and description
3. Get page and verify changes
4. Export page as HTML
5. Delete page (cleanup)
6. Simulates: CMS-like content publishing

### User Provisioning
1. List current users
2. Create new user
3. Verify user in list
4. Update user name
5. Deactivate user
6. Delete user
7. Simulates: automated user onboarding/offboarding

---

## Test Results

### Full Test Run — `pytest -v --tb=no`

```
platform darwin -- Python 3.13.2, pytest-9.0.2
rootdir: /Users/gldc/Developer/wiki/agent-harness
collected 43 items

wiki_cli/tests/test_core.py::TestSession::test_create_session PASSED
wiki_cli/tests/test_core.py::TestSession::test_record_operation PASSED
wiki_cli/tests/test_core.py::TestSession::test_undo PASSED
wiki_cli/tests/test_core.py::TestSession::test_redo PASSED
wiki_cli/tests/test_core.py::TestSession::test_undo_empty PASSED
wiki_cli/tests/test_core.py::TestSession::test_redo_empty PASSED
wiki_cli/tests/test_core.py::TestSession::test_clear_history PASSED
wiki_cli/tests/test_core.py::TestSession::test_history_limit PASSED
wiki_cli/tests/test_core.py::TestSession::test_save_load_roundtrip PASSED
wiki_cli/tests/test_core.py::TestSession::test_status_dict PASSED
wiki_cli/tests/test_core.py::TestSession::test_record_clears_redo PASSED
wiki_cli/tests/test_core.py::TestBackend::test_load_config_default PASSED
wiki_cli/tests/test_core.py::TestBackend::test_load_config_env_override PASSED
wiki_cli/tests/test_core.py::TestBackend::test_save_and_reload_config PASSED
wiki_cli/tests/test_core.py::TestBackend::test_validate_config_missing_url PASSED
wiki_cli/tests/test_core.py::TestBackend::test_validate_config_missing_key PASSED
wiki_cli/tests/test_core.py::TestBackend::test_client_init PASSED
wiki_cli/tests/test_core.py::TestBackend::test_client_url_strip_trailing_slash PASSED
wiki_cli/tests/test_core.py::TestPageModule::test_query_strings_not_empty PASSED
wiki_cli/tests/test_core.py::TestPageModule::test_update_page_field_map PASSED
wiki_cli/tests/test_core.py::TestExportModule::test_export_markdown PASSED
wiki_cli/tests/test_core.py::TestExportModule::test_export_html PASSED
wiki_cli/tests/test_core.py::TestExportModule::test_export_json PASSED
wiki_cli/tests/test_core.py::TestExportModule::test_export_no_overwrite PASSED
wiki_cli/tests/test_core.py::TestCLI::test_help PASSED
wiki_cli/tests/test_core.py::TestCLI::test_version PASSED
wiki_cli/tests/test_core.py::TestCLI::test_page_group_help PASSED
wiki_cli/tests/test_core.py::TestCLI::test_all_groups_registered PASSED
wiki_cli/tests/test_full_e2e.py::TestWikiE2E::test_connection SKIPPED
wiki_cli/tests/test_full_e2e.py::TestWikiE2E::test_system_info SKIPPED
wiki_cli/tests/test_full_e2e.py::TestWikiE2E::test_page_lifecycle SKIPPED
wiki_cli/tests/test_full_e2e.py::TestWikiE2E::test_list_pages SKIPPED
wiki_cli/tests/test_full_e2e.py::TestWikiE2E::test_list_users SKIPPED
wiki_cli/tests/test_full_e2e.py::TestWikiE2E::test_list_groups SKIPPED
wiki_cli/tests/test_full_e2e.py::TestWikiE2E::test_site_config SKIPPED
wiki_cli/tests/test_full_e2e.py::TestWikiE2E::test_tags SKIPPED
wiki_cli/tests/test_full_e2e.py::TestWikiE2E::test_page_tree SKIPPED
wiki_cli/tests/test_full_e2e.py::TestWikiE2E::test_export_page_html SKIPPED
wiki_cli/tests/test_full_e2e.py::TestCLISubprocess::test_help PASSED
wiki_cli/tests/test_full_e2e.py::TestCLISubprocess::test_version PASSED
wiki_cli/tests/test_full_e2e.py::TestCLISubprocess::test_json_site_info SKIPPED
wiki_cli/tests/test_full_e2e.py::TestCLISubprocess::test_json_page_list SKIPPED
wiki_cli/tests/test_full_e2e.py::TestCLISubprocess::test_full_workflow SKIPPED

======================== 30 passed, 13 skipped in 0.21s ========================
```

### Summary Statistics
- **Total tests:** 43
- **Passed:** 30 (100% of runnable tests)
- **Skipped:** 13 (require running Wiki.js instance — set `WIKI_URL` and `WIKI_API_KEY`)
- **Failed:** 0
- **Execution time:** 0.21s

### Subprocess Test Verification
```
WIKI_CLI_FORCE_INSTALLED=1 run:
[_resolve_cli] Using installed command: /opt/homebrew/Caskroom/miniconda/base/bin/wiki-cli
2 passed, 3 skipped (Wiki.js-dependent)
```

### Coverage Notes
- Session module: 11/11 tests — full coverage of undo/redo, save/load, history
- Backend module: 7/7 tests — config, validation, client initialization
- Page module: 2/2 tests — query strings, field mapping
- Export module: 4/4 tests — markdown, HTML, JSON export with mock client
- CLI module: 4/4 tests — help, version, groups, all commands registered
- Subprocess tests: 2/2 passed — help and version via installed binary
- E2E Wiki.js tests: 10 tests ready for when Wiki.js instance is available
