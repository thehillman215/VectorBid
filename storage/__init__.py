"""
Minimal storage abstraction.

Right now it only supports saving files to ./data on local disk.
Later we can swap in S3, Azure, etc. by adding new classes that
implement the same 3-method interface.
"""

from pathlib import Path
from typing import Protocol, BinaryIO


class StorageBackend(Protocol):
    """Interface every storage backend must implement."""
    def save(self, key: str, fp: BinaryIO) -> None: ...
    def open(self, key: str, mode: str = "rb") -> BinaryIO: ...
    def exists(self, key: str) -> bool: ...


class LocalDisk(StorageBackend):
    """Super-simple ‘put it in ./data’ backend."""
    def __init__(self, root: str | Path = "data"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    # helper
    def _path(self, key: str) -> Path:
        return self.root / key

    # StorageBackend API
    def save(self, key: str, fp: BinaryIO) -> None:
        dest = self._path(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as out:
            out.write(fp.read())

    def open(self, key: str, mode: str = "rb") -> BinaryIO:
        return self._path(key).open(mode)

    def exists(self, key: str) -> bool:
        return self._path(key).exists()


# singleton the rest of the app can import:
disk_storage: StorageBackend = LocalDisk()
