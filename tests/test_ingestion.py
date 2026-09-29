from __future__ import annotations

from datetime import date
from pathlib import Path
import sqlite3
import tempfile
import unittest

from taxbot.errors import ValidationError
from taxbot.ingestion import (
    StatementExtraction,
    StatementIngestionService,
    StatementObservation,
)
from taxbot.ledger import LedgerService
from taxbot.storage import StoragePolicy
from taxbot.util import request_hash


class StatementIngestionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "synthetic"
        self.ledger = LedgerService(StoragePolicy(self.root, Path.cwd()))
        self.actor = "synthetic-ingestion-tester"
        self.taxpayer_id = self.ledger.create_taxpayer(
            residency_status="resident",
            idempotency_key="taxpayer",
            expected_revision=0,
            actor=self.actor,
        )
        self.account_id = self.ledger.create_financial_account(
            taxpayer_id=self.taxpayer_id,
            institution="Synthetic Bank",
            account_kind="current_salaried",
            currency="PKR",
            idempotency_key="account",
            expected_revision=self.ledger.ledger_revision,
            actor=self.actor,
        )
        self.document_id = self.ledger.register_document(
            content=b"%PDF-1.7\n% deliberately synthetic searchable statement fixture\n",
            mime_type="application/pdf",
            document_kind="bank_statement",
            idempotency_key="statement-document",
            expected_revision=self.ledger.ledger_revision,
            actor=self.actor,
        )
        self.ingestion = StatementIngestionService(self.ledger.database)
        self.configuration_digest = request_hash(
            {"fixture": "synthetic-searchable-statement-v1"}
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def observation(
        locator: str,
        transaction_date: date,
        direction: str,
        amount_minor: int,
        balance_minor: int,
        narration: str,
        reference: str | None = None,
    ) -> StatementObservation:
        return StatementObservation(
            source_locator=locator,
            transaction_date=transaction_date,
            narration=narration,
            direction=direction,
            amount_minor=amount_minor,
            running_balance_minor=balance_minor,
            bank_reference=reference,
            raw_fields={"synthetic": narration},
            normalized_fields={"narration": narration},
            extraction_confidence="0.99",
        )

    def extraction(
        self,
        *observations: StatementObservation,
        start: date = date(2026, 7, 1),
        end: date = date(2026, 7, 31),
        opening: int = 10_000,
        closing: int | None = None,
    ) -> StatementExtraction:
        debits = sum(item.amount_minor for item in observations if item.direction == "debit")
        credits = sum(item.amount_minor for item in observations if item.direction == "credit")
        return StatementExtraction(
            statement_start=start,
            statement_end=end,
            currency="PKR",
            opening_balance_minor=opening,
            closing_balance_minor=(opening + credits - debits if closing is None else closing),
            declared_debits_minor=debits,
            declared_credits_minor=credits,
            layout_signature="synthetic-searchable-pdf-v1",
            observations=tuple(observations),
        )

    def stage(self, key: str, extraction: StatementExtraction) -> dict[str, object]:
        return self.ingestion.stage_extraction(
            document_id=self.document_id,
            financial_account_id=self.account_id,
            adapter_id="synthetic_searchable_pdf",
            adapter_version="1",
            extractor_id="synthetic_text_layer",
            extractor_version="1",
            configuration_digest=self.configuration_digest,
            run_key=key,
            extraction=extraction,
            idempotency_key=f"stage-{key}",
            expected_revision=self.ledger.ledger_revision,
            actor=self.actor,
        )

    def publish(self, batch_id: str, key: str) -> dict[str, object]:
        return self.ingestion.publish_batch(
            batch_id=batch_id,
            idempotency_key=f"publish-{key}",
            expected_revision=self.ledger.ledger_revision,
            actor=self.actor,
        )

    def test_controlled_batch_is_idempotent_and_published_atomically(self) -> None:
        extraction = self.extraction(
            self.observation(
                "page:1/row:1", date(2026, 7, 2), "credit", 50_000, 60_000, "SYNTHETIC SALARY", "REF-1"
            ),
            self.observation(
                "page:1/row:2", date(2026, 7, 3), "debit", 20_000, 40_000, "SYNTHETIC TRANSFER", "REF-2"
            ),
        )
        staged = self.stage("july", extraction)
        self.assertEqual(staged["state"], "ready")
        revision = self.ledger.ledger_revision
        repeated = self.ingestion.stage_extraction(
            document_id=self.document_id,
            financial_account_id=self.account_id,
            adapter_id="synthetic_searchable_pdf",
            adapter_version="1",
            extractor_id="synthetic_text_layer",
            extractor_version="1",
            configuration_digest=self.configuration_digest,
            run_key="july",
            extraction=extraction,
            idempotency_key="stage-july",
            expected_revision=revision - 1,
            actor=self.actor,
        )
        self.assertEqual(staged, repeated)
        reused = self.ingestion.stage_extraction(
            document_id=self.document_id,
            financial_account_id=self.account_id,
            adapter_id="synthetic_searchable_pdf",
            adapter_version="1",
            extractor_id="synthetic_text_layer",
            extractor_version="1",
            configuration_digest=self.configuration_digest,
            run_key="july",
            extraction=extraction,
            idempotency_key="stage-july-alternate-command",
            expected_revision=self.ledger.ledger_revision,
            actor=self.actor,
        )
        self.assertEqual(reused["batch_id"], staged["batch_id"])
        self.assertTrue(reused["reused"])
        self.assertEqual(self.ledger.ledger_revision, revision)
        with self.ledger.database.connect(readonly=True) as connection:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM source_observations").fetchone()[0],
                2,
            )
        conflicting = self.extraction(
            self.observation(
                "page:1/row:1", date(2026, 7, 2), "credit", 51_000, 61_000, "SYNTHETIC SALARY", "REF-1"
            ),
            self.observation(
                "page:1/row:2", date(2026, 7, 3), "debit", 20_000, 41_000, "SYNTHETIC TRANSFER", "REF-2"
            ),
        )
        before_conflict = self.ledger.ledger_revision
        with self.assertRaises(ValidationError):
            self.ingestion.stage_extraction(
                document_id=self.document_id,
                financial_account_id=self.account_id,
                adapter_id="synthetic_searchable_pdf",
                adapter_version="1",
                extractor_id="synthetic_text_layer",
                extractor_version="1",
                configuration_digest=self.configuration_digest,
                run_key="july",
                extraction=conflicting,
                idempotency_key="stage-july-conflicting-content",
                expected_revision=before_conflict,
                actor=self.actor,
            )
        self.assertEqual(self.ledger.ledger_revision, before_conflict)
        result = self.publish(str(staged["batch_id"]), "july")
        self.assertEqual(result["published_count"], 2)
        with self.ledger.database.connect(readonly=True) as connection:
            published = connection.execute(
                "SELECT COUNT(*) FROM published_observations WHERE batch_id = ?",
                (staged["batch_id"],),
            ).fetchone()[0]
            journals = connection.execute("SELECT COUNT(*) FROM journal_entries").fetchone()[0]
        self.assertEqual(published, 2)
        self.assertEqual(journals, 0)

    def test_overlap_creates_candidates_without_deleting_equal_transactions(self) -> None:
        first = self.extraction(
            self.observation(
                "page:1/row:1", date(2026, 7, 30), "debit", 1_000, 9_000, "SYNTHETIC WALLET", "SAME-REF"
            )
        )
        first_batch = self.stage("overlap-a", first)
        self.publish(str(first_batch["batch_id"]), "overlap-a")

        second = self.extraction(
            self.observation(
                "page:1/row:4", date(2026, 7, 30), "debit", 1_000, 9_000, "SYNTHETIC WALLET", "SAME-REF"
            ),
            self.observation(
                "page:1/row:5", date(2026, 7, 31), "debit", 1_000, 8_000, "SYNTHETIC WALLET"
            ),
            opening=10_000,
        )
        second_batch = self.stage("overlap-b", second)
        result = self.publish(str(second_batch["batch_id"]), "overlap-b")
        self.assertGreaterEqual(int(result["duplicate_candidate_count"]), 1)
        with self.ledger.database.connect(readonly=True) as connection:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM published_observations").fetchone()[0],
                3,
            )
            self.assertGreaterEqual(
                connection.execute("SELECT COUNT(*) FROM duplicate_candidates").fetchone()[0],
                1,
            )

    def test_balance_mismatch_quarantines_and_cannot_publish(self) -> None:
        malformed = self.extraction(
            self.observation(
                "page:1/row:1", date(2026, 7, 2), "debit", 1_000, 8_500, "SYNTHETIC BAD CONTROL"
            ),
            closing=8_500,
        )
        staged = self.stage("bad-controls", malformed)
        self.assertEqual(staged["state"], "quarantined")
        self.assertIn("running_balance_mismatch", staged["diagnostics"])
        before = self.ledger.ledger_revision
        with self.assertRaises(ValidationError):
            self.publish(str(staged["batch_id"]), "bad-controls")
        self.assertEqual(self.ledger.ledger_revision, before)
        with self.ledger.database.connect(readonly=True) as connection:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM published_observations").fetchone()[0],
                0,
            )

    def test_adapter_format_drift_diagnostic_quarantines(self) -> None:
        changed = StatementExtraction(
            statement_start=date(2026, 7, 1),
            statement_end=date(2026, 7, 31),
            currency="PKR",
            opening_balance_minor=None,
            closing_balance_minor=None,
            declared_debits_minor=None,
            declared_credits_minor=None,
            layout_signature="unrecognized-synthetic-layout",
            observations=(),
            diagnostics=("unknown_layout_signature",),
        )
        staged = self.stage("format-drift", changed)
        self.assertEqual(staged["state"], "quarantined")
        self.assertIn("unknown_layout_signature", staged["diagnostics"])

    def test_unreadable_normalized_fields_are_retained_in_quarantine(self) -> None:
        unreadable = StatementExtraction(
            statement_start=date(2026, 7, 1),
            statement_end=date(2026, 7, 31),
            currency="PKR",
            opening_balance_minor=10_000,
            closing_balance_minor=10_000,
            declared_debits_minor=0,
            declared_credits_minor=0,
            layout_signature="synthetic-searchable-pdf-v1",
            observations=(
                StatementObservation(
                    source_locator="page:1/text-span:bad",
                    transaction_date=None,
                    narration="SYNTHETIC UNREADABLE ROW",
                    direction="ambiguous",
                    amount_minor=None,
                    running_balance_minor=None,
                    raw_fields={"synthetic": "unreadable"},
                    normalized_fields={},
                    extraction_confidence="0.2",
                ),
            ),
        )
        staged = self.stage("unreadable", unreadable)
        self.assertEqual(staged["state"], "quarantined")
        self.assertIn("ambiguous_direction", staged["diagnostics"])
        self.assertIn("invalid_amount", staged["diagnostics"])
        self.assertIn("missing_transaction_date", staged["diagnostics"])
        with self.ledger.database.connect(readonly=True) as connection:
            row = connection.execute(
                "SELECT transaction_date, direction, amount_minor FROM source_observations"
            ).fetchone()
        self.assertEqual(tuple(row), (None, "unknown", None))

    def test_cross_year_rows_and_reversal_are_retained(self) -> None:
        extraction = self.extraction(
            self.observation(
                "page:1/row:1", date(2026, 6, 30), "debit", 2_000, 8_000, "SYNTHETIC ORIGINAL", "REV-1"
            ),
            self.observation(
                "page:1/row:2", date(2026, 7, 1), "credit", 2_000, 10_000, "SYNTHETIC REVERSAL", "REV-2"
            ),
            start=date(2026, 6, 30),
            end=date(2026, 7, 1),
        )
        staged = self.stage("year-boundary", extraction)
        self.publish(str(staged["batch_id"]), "year-boundary")
        with self.ledger.database.connect(readonly=True) as connection:
            rows = connection.execute(
                "SELECT transaction_date, direction FROM source_observations ORDER BY ordinal"
            ).fetchall()
        self.assertEqual([tuple(row) for row in rows], [("2026-06-30", "debit"), ("2026-07-01", "credit")])

    def test_immutable_locator_and_extractor_version_survive_publication(self) -> None:
        extraction = self.extraction(
            self.observation(
                "page:2/text-span:7", date(2026, 7, 5), "credit", 5_000, 15_000, "SYNTHETIC CREDIT"
            )
        )
        staged = self.stage("lineage", extraction)
        self.publish(str(staged["batch_id"]), "lineage")
        with self.ledger.database.connect() as connection:
            row = connection.execute(
                """
                SELECT o.source_locator, r.extractor_id, r.extractor_version
                FROM source_observations o
                JOIN extraction_runs r ON r.id = o.extraction_run_id
                """
            ).fetchone()
            self.assertEqual(tuple(row), ("page:2/text-span:7", "synthetic_text_layer", "1"))
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE source_observations SET source_locator = 'changed'")


if __name__ == "__main__":
    unittest.main()
