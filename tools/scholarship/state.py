"""Read and write the college state file (state/state.json)."""
import json
import os
import tempfile
from datetime import date
from pathlib import Path
from typing import Callable

VERSION = 1
# Key = version migrated *from*; the function returns the state at version + 1.
MIGRATIONS: dict[int, Callable[[dict], dict]] = {}
KEYS = {"version": int, "enrolled_on": str, "steps_done": list, "work": dict}


class CollegeError(Exception):
    """Domain error, with a message readable by the student."""


def init(path: Path, today: date) -> dict:
    """Create the state if absent; never touch an existing one."""
    if path.exists():
        return load(path)
    state = {"version": VERSION, "enrolled_on": today.isoformat(), "steps_done": [], "work": {}}
    save(state, path)
    return state


def _corrupt(path: Path, reason: str) -> CollegeError:
    return CollegeError(
        f"State corrupted: {path} ({reason}). Restore it from the last commit "
        "with `git checkout -- state/state.json` (progress is committed after each step)."
    )


def _check_keys(state, path: Path, when: str = "") -> None:
    if not isinstance(state, dict):
        raise _corrupt(path, f"a JSON object is expected {when}".strip())
    for key, expected in KEYS.items():
        value = state.get(key)
        if not isinstance(value, expected) or isinstance(value, bool):
            raise _corrupt(path, f"key \"{key}\" missing or invalid {when}".strip())


def load(path: Path) -> dict:
    if not path.exists():
        raise CollegeError(f"State not found ({path}): run `college.py init`.")
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise _corrupt(path, f"invalid JSON: {e}") from None
    if not isinstance(state, dict):
        raise _corrupt(path, "a JSON object is expected")
    _check_keys(state, path)
    if state["version"] > VERSION:
        raise CollegeError(
            f"State {path} is version {state['version']}, newer than this engine (version {VERSION}): "
            "update the engine with `git pull engine main`."
        )
    migrated = False
    while state["version"] < VERSION:
        migration = MIGRATIONS.get(state["version"])
        if migration is None:
            raise CollegeError(f"No migration from state version {state['version']} (engine version {VERSION}).")
        state = migration(state)
        state["version"] += 1
        migrated = True
    if migrated:
        _check_keys(state, path, "after migration")
        save(state, path)
    return state


def save(state: dict, path: Path) -> None:
    """Atomic write: a temporary file replaces the old one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    except BaseException:
        os.unlink(tmp)
        raise
