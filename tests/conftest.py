"""Windows-only test compatibility for Bunnyland's POSIX-style checkpoint fsync.

Pinned Bunnyland opens file descriptors read-only before fsync, and attempts
os.open() on directories. Both fail on Windows. The pytest override changes
only these platform-specific durability steps: it retains real file fsync
and leaves the world serialization, checkpoint replacement, and reload
logic untouched. It does not make production persistence Windows-safe.
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

    def skip_unsupported_directory_fsync(path: Path) -> None:
        # POSIX permits opening a directory for fsync; Python's ordinary
        # Windows os.open() does not. Preserve file sync and real save/load
        # behavior, but skip this unsupported durability operation in tests.
        assert path.is_dir()

    monkeypatch.setattr(persistence, "_fsync_file", fsync_with_writable_handle)
    monkeypatch.setattr(persistence, "_fsync_directory", skip_unsupported_directory_fsync)
