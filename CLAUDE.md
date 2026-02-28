# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

**Run all tests with coverage:**
```
tox
```

**Run tests only (no coverage/style):**
```
tox -e cover
# or directly:
pytest
```

**Run a specific test:**
```
pytest tests/test_commands.py::test_name
# or using wst:
wst test -k test_filter
```

**Run style checks:**
```
tox -e style
```

**Install in development mode:**
```
pip install -e .
```

## Architecture

This is a Python CLI tool (`wst`) that wraps git and tox to simplify multi-repo workspace management.

### Entry Point
`workspace/controller.py` — `Commander` class is the main CLI entry point (`Commander.main()`). It dynamically loads all command classes, sets up argparse subcommands, and dispatches to the appropriate command's `run()` method.

### Command Pattern
All commands live in `workspace/commands/` and inherit from `AbstractCommand` (`workspace/commands/__init__.py`). Each command:
- Defines its CLI args via `arguments()` classmethod
- Implements `run()` for execution
- Optionally sets `alias` for a short alias (e.g., `ci` for `commit`)

Commands support "chaining" — returning a tuple of two arg lists from `arguments()` where the second list are chain options that trigger other commands after the main one runs.

### Key Modules
- `workspace/scm.py` — All git operations (branch detection, commit, push, remote management, etc.)
- `workspace/commands/helpers.py` — `ToxIni` class (parses tox.ini for test env management) and `ProductPager` (multi-repo pager output)
- `workspace/config.py` — User config via `localconfig`/`remoteconfig` (`~/.config/workspace.cfg`)
- `workspace/utils.py` — Shared utilities including path helpers and `log_exception`

### Testing Approach
Tests use `pytest` with `pytest-xdist` (4 parallel workers). The `conftest.py` provides two key fixtures:
- `wst` — invokes the full CLI via `Commander().run()` with monkeypatched `sys.argv`
- `mock_run` — mocks out subprocess calls (`utils_core.process.run`, `workspace.scm.run`, etc.) for unit testing commands without executing real git/tox commands

### Tox Configuration
`tox.ini` uses a single shared `[testenv]` with all deps consolidated (no separate test/style/cover envs for deps). The `cover` env uses `env_dir = {work_dir}/workspace-tools` to place the virtualenv in the tox work directory. `recreate = False` and `skipsdist = True` speed up repeated runs.
