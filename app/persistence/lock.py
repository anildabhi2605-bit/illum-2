"""Cross-process OS-level file locking for ILLUM AI STUDIO (P03-T02).

Governed by:
- Windows 10/11 primary target compatibility (msvcrt)
- POSIX secondary target compatibility (fcntl)
- Fail-closed locking behavior during migrations, recovery, and startup inspection
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from typing import BinaryIO, Generator, Optional


class DatabaseLockedError(RuntimeError):
    """Raised when an exclusive database lock cannot be acquired due to another running process."""
    pass


class FileLock:
    """Cross-platform OS-level non-blocking file lock."""

    def __init__(self, lock_file_path: Path) -> None:
        self.lock_file_path = lock_file_path
        self._file_handle: Optional[BinaryIO] = None

    def acquire(self) -> None:
        """Acquire exclusive non-blocking lock. Raises DatabaseLockedError if locked."""
        # Ensure parent directory exists
        self.lock_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize lock file with 1 sentinel byte if missing or empty
        if not self.lock_file_path.exists() or self.lock_file_path.stat().st_size == 0:
            with open(self.lock_file_path, "wb") as f_init:
                f_init.write(b"\x00")
                f_init.flush()

        # Open in read-write binary mode
        f = open(self.lock_file_path, "r+b")
        self._file_handle = f

        try:
            if sys.platform == "win32":
                import msvcrt
                f.seek(0)
                # Non-blocking lock on 1 byte at offset 0
                msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                # Non-blocking exclusive lock on file descriptor
                fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, IOError) as exc:
            f.close()
            self._file_handle = None
            raise DatabaseLockedError(
                f"Another ILLUM AI STUDIO process holds the database lock at {self.lock_file_path}."
            ) from exc

    def release(self) -> None:
        """Release OS-level lock and close file handle."""
        if self._file_handle is not None and not self._file_handle.closed:
            try:
                if sys.platform == "win32":
                    import msvcrt
                    self._file_handle.seek(0)
                    msvcrt.locking(self._file_handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(self._file_handle.fileno(), fcntl.LOCK_UN)
            except (OSError, IOError):
                pass
            finally:
                self._file_handle.close()
                self._file_handle = None

    def __enter__(self) -> "FileLock":
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.release()


@contextmanager
def database_lock(lock_path: Optional[Path] = None) -> Generator[FileLock, None, None]:
    """Context manager for acquiring cross-process exclusive database lock."""
    target_lock = lock_path if lock_path is not None else Path("data/illum.lock")
    lock = FileLock(target_lock)
    lock.acquire()
    try:
        yield lock
    finally:
        lock.release()
