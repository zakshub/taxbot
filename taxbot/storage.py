"""Private-root policy and Windows BitLocker verification."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from .errors import StorageSecurityError


class StorageMode(StrEnum):
    SYNTHETIC = "synthetic"
    REAL = "real"


class EncryptionVerifier(Protocol):
    def verify(self, root: Path) -> None: ...


class WindowsBitLockerVerifier:
    """Fail-closed BitLocker check using the native PowerShell cmdlet."""

    def verify(self, root: Path) -> None:
        if os.name != "nt":
            raise StorageSecurityError("BitLocker verification is supported only on Windows")
        mount_point = root.anchor.rstrip("\\")
        if not mount_point:
            raise StorageSecurityError("Private root has no Windows volume")
        command = (
            "$v = Get-BitLockerVolume -MountPoint '"
            + mount_point.replace("'", "''")
            + "'; if ($null -eq $v) { exit 2 }; "
            "[pscustomobject]@{VolumeStatus=$v.VolumeStatus.ToString();"
            "ProtectionStatus=$v.ProtectionStatus.ToString()} | ConvertTo-Json -Compress"
        )
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise StorageSecurityError("Unable to inspect BitLocker status") from exc
        if result.returncode != 0:
            raise StorageSecurityError("BitLocker status is unavailable for the private volume")
        try:
            status = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise StorageSecurityError("BitLocker returned an unreadable status") from exc
        if status.get("VolumeStatus") != "FullyEncrypted":
            raise StorageSecurityError("Private volume is not fully BitLocker encrypted")
        if status.get("ProtectionStatus") != "On":
            raise StorageSecurityError("BitLocker protection is not on")


@dataclass(frozen=True, slots=True)
class StoragePolicy:
    root: Path
    repository_root: Path
    mode: StorageMode = StorageMode.SYNTHETIC
    encryption_verifier: EncryptionVerifier | None = None

    @property
    def resolved_root(self) -> Path:
        return Path(self.root).resolve()

    @property
    def database_path(self) -> Path:
        return self.resolved_root / "ledger.sqlite3"

    @property
    def objects_root(self) -> Path:
        return self.resolved_root / "objects"

    @property
    def backups_root(self) -> Path:
        return self.resolved_root / "backups"

    @property
    def restore_receipt_path(self) -> Path:
        return self.resolved_root / ".taxbot" / "restore-receipt.json"

    def preflight(self, *, require_restore_receipt: bool = True) -> None:
        root = self.resolved_root
        repo = Path(self.repository_root).resolve()
        if self.mode == StorageMode.SYNTHETIC:
            root.mkdir(parents=True, exist_ok=True)
            return
        if root == repo or root.is_relative_to(repo) or repo.is_relative_to(root):
            raise StorageSecurityError("Real-data root must be separate from the repository")
        for sync_root in self._known_sync_roots():
            if root == sync_root or root.is_relative_to(sync_root):
                raise StorageSecurityError("Real-data root must not be inside a sync folder")
        if not root.exists() or not root.is_dir():
            raise StorageSecurityError("Real-data root must already exist on the encrypted volume")
        verifier = self.encryption_verifier or WindowsBitLockerVerifier()
        verifier.verify(root)
        if require_restore_receipt:
            self._verify_restore_receipt()

    def prepare_directories(self, *, setup_only: bool = False) -> None:
        self.preflight(require_restore_receipt=not setup_only)
        self.objects_root.mkdir(parents=True, exist_ok=True)
        self.backups_root.mkdir(parents=True, exist_ok=True)
        (self.resolved_root / ".taxbot").mkdir(parents=True, exist_ok=True)

    def _verify_restore_receipt(self) -> None:
        receipt_path = self.restore_receipt_path
        if not receipt_path.is_file():
            raise StorageSecurityError("A verified restore receipt is required before real-data use")
        try:
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            verified_at = datetime.fromisoformat(receipt["verified_at"].replace("Z", "+00:00"))
            manifest_hash = receipt["backup_manifest_hash"]
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            raise StorageSecurityError("Restore receipt is invalid") from exc
        if verified_at.tzinfo is None or verified_at > datetime.now(UTC):
            raise StorageSecurityError("Restore receipt timestamp is invalid")
        if not isinstance(manifest_hash, str) or len(manifest_hash) != 64:
            raise StorageSecurityError("Restore receipt manifest hash is invalid")

    @staticmethod
    def _known_sync_roots() -> set[Path]:
        candidates: set[Path] = set()
        for name in ("OneDrive", "OneDriveCommercial", "OneDriveConsumer", "Dropbox"):
            value = os.environ.get(name)
            if value:
                candidates.add(Path(value).resolve())
        home = Path.home()
        for name in ("OneDrive", "Dropbox", "Google Drive"):
            candidate = home / name
            if candidate.exists():
                candidates.add(candidate.resolve())
        return candidates
