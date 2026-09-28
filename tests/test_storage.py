from datetime import UTC, datetime
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from taxbot.errors import StorageSecurityError
from taxbot.storage import StorageMode, StoragePolicy, WindowsBitLockerVerifier


class PassingVerifier:
    def __init__(self) -> None:
        self.calls: list[Path] = []

    def verify(self, root: Path) -> None:
        self.calls.append(root)


class StorageTests(unittest.TestCase):
    def test_real_data_root_cannot_be_repository(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy = StoragePolicy(
                root=root,
                repository_root=root,
                mode=StorageMode.REAL,
                encryption_verifier=PassingVerifier(),
            )
            with self.assertRaises(StorageSecurityError):
                policy.preflight(require_restore_receipt=False)

    def test_real_mode_requires_encryption_and_restore_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir, tempfile.TemporaryDirectory() as repo_dir:
            verifier = PassingVerifier()
            policy = StoragePolicy(
                root=Path(root_dir),
                repository_root=Path(repo_dir),
                mode=StorageMode.REAL,
                encryption_verifier=verifier,
            )
            policy.preflight(require_restore_receipt=False)
            self.assertEqual(verifier.calls, [Path(root_dir).resolve()])
            with self.assertRaises(StorageSecurityError):
                policy.preflight(require_restore_receipt=True)
            policy.restore_receipt_path.parent.mkdir(parents=True)
            policy.restore_receipt_path.write_text(
                json.dumps(
                    {
                        "backup_manifest_hash": "a" * 64,
                        "verified_at": datetime.now(UTC).isoformat(),
                    }
                ),
                encoding="utf-8",
            )
            policy.preflight(require_restore_receipt=True)

    def test_synthetic_mode_can_use_isolated_temporary_root(self) -> None:
        with tempfile.TemporaryDirectory() as root_dir:
            root = Path(root_dir) / "synthetic"
            policy = StoragePolicy(root=root, repository_root=Path.cwd())
            policy.prepare_directories()
            self.assertTrue(policy.objects_root.is_dir())
            self.assertTrue(policy.backups_root.is_dir())

    def test_real_data_root_cannot_be_inside_known_sync_root(self) -> None:
        with tempfile.TemporaryDirectory() as sync_dir, tempfile.TemporaryDirectory() as repo_dir:
            root = Path(sync_dir) / "private"
            root.mkdir()
            policy = StoragePolicy(
                root=root,
                repository_root=Path(repo_dir),
                mode=StorageMode.REAL,
                encryption_verifier=PassingVerifier(),
            )
            with patch.dict(os.environ, {"OneDrive": sync_dir}):
                with self.assertRaises(StorageSecurityError):
                    policy.preflight(require_restore_receipt=False)

    @unittest.skipUnless(os.name == "nt", "BitLocker verifier is Windows-specific")
    def test_bitlocker_verifier_requires_full_encryption_and_protection(self) -> None:
        verifier = WindowsBitLockerVerifier()
        success = SimpleNamespace(
            returncode=0,
            stdout='{"VolumeStatus":"FullyEncrypted","ProtectionStatus":"On"}',
        )
        with patch("taxbot.storage.subprocess.run", return_value=success):
            verifier.verify(Path("C:/synthetic"))
        disabled = SimpleNamespace(
            returncode=0,
            stdout='{"VolumeStatus":"FullyEncrypted","ProtectionStatus":"Off"}',
        )
        with patch("taxbot.storage.subprocess.run", return_value=disabled):
            with self.assertRaises(StorageSecurityError):
                verifier.verify(Path("C:/synthetic"))


if __name__ == "__main__":
    unittest.main()
