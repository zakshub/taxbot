"""Content-addressed immutable document-object storage."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from .errors import ValidationError
from .util import sha256_bytes


class DocumentStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def put(self, content: bytes) -> tuple[str, str]:
        digest = sha256_bytes(content)
        relative = Path(digest[:2]) / digest[2:4] / digest
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if target.read_bytes() != content:
                raise ValidationError("Document hash collision or corrupt object")
            return digest, relative.as_posix()
        handle, temp_name = tempfile.mkstemp(prefix=".object-", dir=target.parent)
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temp_name, target)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        return digest, relative.as_posix()

    def read_verified(self, relative_path: str, expected_hash: str) -> bytes:
        target = (self.root / relative_path).resolve()
        if not target.is_relative_to(self.root):
            raise ValidationError("Document path escapes object store")
        content = target.read_bytes()
        if sha256_bytes(content) != expected_hash:
            raise ValidationError("Document object hash mismatch")
        return content
