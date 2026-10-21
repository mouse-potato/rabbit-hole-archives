"""Test-only compatibility shim for a Bunnyland Windows checkpoint bug.

Pinned Bunnyland opens checkpoint files as "rb" before os.fsync(). Windows
requires a writable descriptor for this operation (OSError: [Errno 9]).
Keep real fsync and real Bunnyland save/load semantics in the tests; only
the file open mode changes, and only on Windows. This does NOT repair the
upstream persistence implementation for application runtime use.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def windows_bunnyland_checkpoint_fsync(monkeypatch: pytest.MonkeyPatch) -> None:
    if sys.platform != "win32":
        return

    import bunnyland.persistence as persistence

    def fsync_with_writable_handle(path: Path) -> None:
        with path.open("r+b") as handle:
            os.fsync(handle.fileno())

    monkeypatch.setattr(persistence, "_fsync_file", fsync_with_writable_handle)
