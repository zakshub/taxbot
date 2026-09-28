"""Consistent local snapshots, verification, and isolated restore drills."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path

from .database import Database
from .errors import BackupError
from .storage import StoragePolicy
from .util import canonical_json, new_id, sha256_bytes, utc_now


class BackupManager:
    def __init__(self, policy: StoragePolicy) -> None:
        self.policy = policy

    def create(self) -> Path:
        self.policy.preflight(require_restore_receipt=False)
        source_db = Database(self.policy.database_path)
        source_db.validate_invariants()
        backup_id = new_id()
        final = self.policy.backups_root / backup_id
        final.parent.mkdir(parents=True, exist_ok=True)
        staging = Path(tempfile.mkdtemp(prefix=".backup-", dir=final.parent))
        try:
            db_target = staging / "ledger.sqlite3"
            with source_db.connect(readonly=True) as source, closing(
                sqlite3.connect(db_target)
            ) as target:
                source.backup(target)
            objects_target = staging / "objects"
            objects_target.mkdir()
            self._copy_referenced_objects(db_target, objects_target)
            files: dict[str, str] = {}
            for path in sorted(p for p in staging.rglob("*") if p.is_file()):
                relative = path.relative_to(staging).as_posix()
                files[relative] = sha256_bytes(path.read_bytes())
            manifest = {
                "schema": 1,
                "backup_id": backup_id,
                "created_at": utc_now(),
                "ledger_revision": source_db.ledger_revision(),
                "schema_version": source_db.schema_version(),
                "files": files,
            }
            manifest_text = canonical_json(manifest)
            (staging / "manifest.json").write_text(manifest_text, encoding="utf-8")
            (staging / "manifest.sha256").write_text(
                sha256_bytes(manifest_text.encode("utf-8")), encoding="ascii"
            )
            os.replace(staging, final)
            return final
        except Exception as exc:
            shutil.rmtree(staging, ignore_errors=True)
            if isinstance(exc, BackupError):
                raise
            raise BackupError("Backup creation failed") from exc

    def verify(self, backup_dir: Path) -> dict[str, int | str]:
        backup = Path(backup_dir).resolve()
        if not backup.is_relative_to(self.policy.backups_root.resolve()):
            raise BackupError("Backup must be inside the protected backup root")
        try:
            manifest_bytes = (backup / "manifest.json").read_bytes()
            expected_manifest_hash = (backup / "manifest.sha256").read_text(
                encoding="ascii"
            )
            actual_manifest_hash = sha256_bytes(manifest_bytes)
            if actual_manifest_hash != expected_manifest_hash:
                raise BackupError("Backup manifest hash mismatch")
            manifest = json.loads(manifest_bytes)
            for relative, expected in manifest["files"].items():
                path = (backup / relative).resolve()
                if not path.is_relative_to(backup) or sha256_bytes(path.read_bytes()) != expected:
                    raise BackupError("Backup file verification failed")
            validation = Database(backup / "ledger.sqlite3").validate_invariants()
            self._verify_referenced_objects(backup / "ledger.sqlite3", backup / "objects")
        except (OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise BackupError("Backup verification failed") from exc
        if validation["ledger_revision"] != manifest["ledger_revision"]:
            raise BackupError("Backup ledger revision mismatch")
        return {
            "manifest_hash": actual_manifest_hash,
            "ledger_revision": int(manifest["ledger_revision"]),
            "schema_version": int(manifest["schema_version"]),
        }

    def restore_drill(self, backup_dir: Path, target: Path) -> dict[str, int | str]:
        self.policy.preflight(require_restore_receipt=False)
        result = self.verify(backup_dir)
        destination = Path(target).resolve()
        if destination.exists():
            raise BackupError("Restore target must not already exist")
        if not destination.is_relative_to(self.policy.resolved_root):
            raise BackupError("Restore target must be inside the protected private root")
        source = Path(backup_dir).resolve()
        if destination == source or destination.is_relative_to(source) or source.is_relative_to(destination):
            raise BackupError("Restore target must be isolated from the source backup")
        try:
            destination.mkdir(parents=True)
            shutil.copy2(source / "ledger.sqlite3", destination / "ledger.sqlite3")
            shutil.copytree(source / "objects", destination / "objects")
            restored = Database(destination / "ledger.sqlite3").validate_invariants()
            if restored["ledger_revision"] != result["ledger_revision"]:
                raise BackupError("Restored ledger revision mismatch")
            receipt = {
                "schema": 1,
                "backup_manifest_hash": result["manifest_hash"],
                "verified_at": utc_now(),
                "restored_to": str(destination),
            }
            receipt_path = self.policy.restore_receipt_path
            receipt_path.parent.mkdir(parents=True, exist_ok=True)
            temp = receipt_path.with_suffix(".tmp")
            temp.write_text(canonical_json(receipt), encoding="utf-8")
            os.replace(temp, receipt_path)
            return result
        except Exception as exc:
            if destination.exists():
                shutil.rmtree(destination, ignore_errors=True)
            if isinstance(exc, BackupError):
                raise
            raise BackupError("Restore drill failed") from exc

    def _copy_referenced_objects(self, database_path: Path, target_root: Path) -> None:
        with Database(database_path).connect(readonly=True) as connection:
            rows = connection.execute(
                "SELECT object_relpath, sha256 FROM documents ORDER BY object_relpath"
            ).fetchall()
        source_root = self.policy.objects_root.resolve()
        for row in rows:
            relative = Path(str(row["object_relpath"]))
            source = (source_root / relative).resolve()
            if not source.is_relative_to(source_root):
                raise BackupError("Document path escapes the protected object root")
            content = source.read_bytes()
            if sha256_bytes(content) != row["sha256"]:
                raise BackupError("Source document hash mismatch")
            target = target_root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

    @staticmethod
    def _verify_referenced_objects(database_path: Path, objects_root: Path) -> None:
        resolved_root = objects_root.resolve()
        with Database(database_path).connect(readonly=True) as connection:
            rows = connection.execute(
                "SELECT object_relpath, sha256 FROM documents ORDER BY object_relpath"
            ).fetchall()
        for row in rows:
            path = (resolved_root / str(row["object_relpath"])).resolve()
            if not path.is_relative_to(resolved_root):
                raise BackupError("Backup document path escapes object root")
            try:
                content = path.read_bytes()
            except OSError as exc:
                raise BackupError("Backup is missing a referenced document") from exc
            if sha256_bytes(content) != row["sha256"]:
                raise BackupError("Backup document hash mismatch")
