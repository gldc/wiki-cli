"""Session management with undo/redo for Wiki.js CLI.

Tracks operations performed via the CLI and provides undo/redo
capability for reversible operations.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional


class Operation:
    """A recorded operation with undo information."""

    def __init__(
        self,
        op_type: str,
        description: str,
        undo_data: Optional[dict] = None,
        result: Optional[dict] = None,
    ):
        self.op_type = op_type
        self.description = description
        self.undo_data = undo_data or {}
        self.result = result or {}
        self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "op_type": self.op_type,
            "description": self.description,
            "undo_data": self.undo_data,
            "result": self.result,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Operation":
        op = cls(
            op_type=data["op_type"],
            description=data["description"],
            undo_data=data.get("undo_data", {}),
            result=data.get("result", {}),
        )
        op.timestamp = data.get("timestamp", time.time())
        return op


class Session:
    """Stateful session for Wiki.js CLI operations.

    Tracks connection info, current context, and operation history
    for undo/redo support.
    """

    def __init__(self, session_path: Optional[str] = None):
        self.session_path = session_path
        self.url = ""
        self.api_key = ""
        self.current_page_id: Optional[int] = None
        self.current_page_path: Optional[str] = None
        self.current_locale: str = "en"
        self._history: list[Operation] = []
        self._redo_stack: list[Operation] = []
        self._modified = False

        if session_path and os.path.exists(session_path):
            self.load(session_path)

    @property
    def modified(self) -> bool:
        return self._modified

    def record(
        self,
        op_type: str,
        description: str,
        undo_data: Optional[dict] = None,
        result: Optional[dict] = None,
    ):
        """Record an operation in history."""
        op = Operation(op_type, description, undo_data, result)
        self._history.append(op)
        self._redo_stack.clear()
        self._modified = True

    def undo(self) -> Optional[Operation]:
        """Pop the last operation for undo. Returns the operation or None."""
        if not self._history:
            return None
        op = self._history.pop()
        self._redo_stack.append(op)
        self._modified = True
        return op

    def redo(self) -> Optional[Operation]:
        """Re-apply the last undone operation. Returns the operation or None."""
        if not self._redo_stack:
            return None
        op = self._redo_stack.pop()
        self._history.append(op)
        self._modified = True
        return op

    def history(self, limit: int = 20) -> list[Operation]:
        """Get recent operation history."""
        return list(reversed(self._history[-limit:]))

    def clear_history(self):
        """Clear all operation history."""
        self._history.clear()
        self._redo_stack.clear()
        self._modified = True

    def save(self, path: Optional[str] = None):
        """Save session state to file."""
        path = path or self.session_path
        if not path:
            return
        data = {
            "url": self.url,
            "current_page_id": self.current_page_id,
            "current_page_path": self.current_page_path,
            "current_locale": self.current_locale,
            "history": [op.to_dict() for op in self._history[-100:]],
            "redo_stack": [op.to_dict() for op in self._redo_stack[-50:]],
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        self._modified = False

    def load(self, path: str):
        """Load session state from file."""
        with open(path) as f:
            data = json.load(f)
        self.url = data.get("url", "")
        self.current_page_id = data.get("current_page_id")
        self.current_page_path = data.get("current_page_path")
        self.current_locale = data.get("current_locale", "en")
        self._history = [Operation.from_dict(d) for d in data.get("history", [])]
        self._redo_stack = [Operation.from_dict(d) for d in data.get("redo_stack", [])]
        self._modified = False

    def status(self) -> dict:
        """Get current session status."""
        return {
            "url": self.url,
            "current_page_id": self.current_page_id,
            "current_page_path": self.current_page_path,
            "current_locale": self.current_locale,
            "history_count": len(self._history),
            "redo_count": len(self._redo_stack),
            "modified": self._modified,
        }

    def to_dict(self) -> dict:
        """Full serializable representation."""
        return {
            "status": self.status(),
            "history": [op.to_dict() for op in self._history],
        }
