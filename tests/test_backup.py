from datetime import date
from pathlib import Path
import tempfile
import unittest

from taxbot.backup import BackupManager
from taxbot.database import Database
from taxbot.errors import BackupError
from taxbot.ledger import LedgerService
from taxbot.models import AccountClass, Direction, PostingInput, ProvenanceMethod, ReviewStatus
from taxbot.money import Money
from taxbot.storage import StoragePolicy


class BackupTests(unittest.TestCase):
    def test_consistent_backup_and_isolated_restore(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "synthetic"
            policy = StoragePolicy(root, Path.cwd())
            service = LedgerService(policy)
            taxpayer = service.create_taxpayer(
                residency_status="resident",
                idempotency_key="taxpayer",
                expected_revision=0,
                actor="synthetic-tester",
            )
            cash = service.create_ledger_account(
                taxpayer_id=taxpayer,
                code="cash",
                name="Synthetic cash",
                account_class=AccountClass.ASSET,
                currency_policy="PKR",
                idempotency_key="cash",
                expected_revision=service.ledger_revision,
                actor="synthetic-tester",
            )
            equity = service.create_ledger_account(
                taxpayer_id=taxpayer,
                code="opening-equity",
                name="Synthetic opening equity",
                account_class=AccountClass.EQUITY,
                currency_policy="PKR",
                idempotency_key="equity",
                expected_revision=service.ledger_revision,
                actor="synthetic-tester",
            )
            document = service.register_document(
                content=b"constructed synthetic source",
                mime_type="text/plain",
                document_kind="synthetic",
                idempotency_key="document",
                expected_revision=service.ledger_revision,
                actor="synthetic-tester",
            )
            service.post_journal(
                taxpayer_id=taxpayer,
                effective_date=date(2026, 7, 1),
                event_type="opening",
                postings=(
                    PostingInput(cash, Direction.DEBIT, Money.from_decimal("1000.00", "PKR")),
                    PostingInput(equity, Direction.CREDIT, Money.from_decimal("1000.00", "PKR")),
                ),
                provenance_method=ProvenanceMethod.USER_SUPPLIED,
                review_status=ReviewStatus.VERIFIED,
                idempotency_key="opening",
                expected_revision=service.ledger_revision,
                actor="synthetic-tester",
                evidence=((document, "establishes", "synthetic:opening"),),
            )
            manager = BackupManager(policy)
            backup = manager.create()
            with self.assertRaises(BackupError):
                manager.restore_drill(backup, backup / "nested-restore")
            verified = manager.verify(backup)
            target = root / "restore-drills" / "first"
            restored = manager.restore_drill(backup, target)
            self.assertEqual(restored, verified)
            self.assertTrue((target / "ledger.sqlite3").is_file())
            self.assertTrue(policy.restore_receipt_path.is_file())
            with Database(target / "ledger.sqlite3").connect(readonly=True) as connection:
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0], 1
                )
                self.assertEqual(
                    connection.execute("SELECT COUNT(*) FROM journal_evidence_links").fetchone()[0],
                    1,
                )
                self.assertGreaterEqual(
                    connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0], 5
                )

    def test_document_corruption_invalidates_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "synthetic"
            policy = StoragePolicy(root, Path.cwd())
            service = LedgerService(policy)
            service.create_taxpayer(
                residency_status="resident",
                idempotency_key="taxpayer",
                expected_revision=0,
                actor="synthetic-tester",
            )
            service.register_document(
                content=b"constructed synthetic source",
                mime_type="text/plain",
                document_kind="synthetic",
                idempotency_key="document",
                expected_revision=service.ledger_revision,
                actor="synthetic-tester",
            )
            manager = BackupManager(policy)
            backup = manager.create()
            object_path = next(path for path in (backup / "objects").rglob("*") if path.is_file())
            object_path.write_bytes(b"corrupt")
            with self.assertRaises(BackupError):
                manager.verify(backup)


if __name__ == "__main__":
    unittest.main()
