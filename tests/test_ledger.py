from __future__ import annotations

from datetime import date
from pathlib import Path
import sqlite3
import tempfile
import unittest

from taxbot.errors import (
    IdempotencyConflictError,
    StaleRevisionError,
    UnbalancedJournalError,
    ValidationError,
)
from taxbot.ledger import LedgerService
from taxbot.models import AccountClass, Direction, PostingInput, ProvenanceMethod, ReviewStatus
from taxbot.money import Money
from taxbot.storage import StoragePolicy


class LedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / "synthetic"
        self.service = LedgerService(StoragePolicy(self.root, Path.cwd()))
        self.actor = "synthetic-tester"
        self.taxpayer_id = self.service.create_taxpayer(
            residency_status="resident",
            idempotency_key="taxpayer",
            expected_revision=0,
            actor=self.actor,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def create_ledger_account(
        self,
        code: str,
        account_class: AccountClass,
        financial_account_id: str | None = None,
        currency_policy: str = "PKR",
    ) -> str:
        return self.service.create_ledger_account(
            taxpayer_id=self.taxpayer_id,
            code=code,
            name=f"Synthetic {code}",
            account_class=account_class,
            currency_policy=currency_policy,
            financial_account_id=financial_account_id,
            idempotency_key=f"ledger-{code}",
            expected_revision=self.service.ledger_revision,
            actor=self.actor,
        )

    def post_two_sided(self, key: str, debit: str, credit: str, amount: str = "100.00") -> str:
        money = Money.from_decimal(amount, "PKR")
        return self.service.post_journal(
            taxpayer_id=self.taxpayer_id,
            effective_date=date(2026, 7, 1),
            event_type="synthetic_event",
            postings=(
                PostingInput(debit, Direction.DEBIT, money),
                PostingInput(credit, Direction.CREDIT, money),
            ),
            provenance_method=ProvenanceMethod.USER_SUPPLIED,
            review_status=ReviewStatus.USER_CONFIRMED,
            idempotency_key=key,
            expected_revision=self.service.ledger_revision,
            actor=self.actor,
            description="Invented test event",
        )

    def test_balanced_journal_idempotency_and_redacted_status(self) -> None:
        cash = self.create_ledger_account("cash", AccountClass.ASSET)
        income = self.create_ledger_account("salary", AccountClass.INCOME)
        before = self.service.ledger_revision
        entry = self.post_two_sided("salary-1", cash, income)
        revision = self.service.ledger_revision
        self.assertEqual(revision, before + 1)
        duplicate = self.service.post_journal(
            taxpayer_id=self.taxpayer_id,
            effective_date=date(2026, 7, 1),
            event_type="synthetic_event",
            postings=(
                PostingInput(cash, Direction.DEBIT, Money.from_decimal("100.00", "PKR")),
                PostingInput(income, Direction.CREDIT, Money.from_decimal("100.00", "PKR")),
            ),
            provenance_method=ProvenanceMethod.USER_SUPPLIED,
            review_status=ReviewStatus.USER_CONFIRMED,
            idempotency_key="salary-1",
            expected_revision=before,
            actor=self.actor,
            description="Invented test event",
        )
        self.assertEqual(entry, duplicate)
        self.assertEqual(self.service.ledger_revision, revision)
        status = self.service.operational_status()
        self.assertEqual(status["unbalanced_journals"], 0)
        self.assertNotIn("Invented", str(status))

    def test_idempotency_conflict_and_stale_revision_are_rejected(self) -> None:
        with self.assertRaises(IdempotencyConflictError):
            self.service.create_taxpayer(
                residency_status="resident",
                idempotency_key="taxpayer",
                expected_revision=0,
                actor="different-synthetic-actor",
            )
        cash = self.create_ledger_account("cash", AccountClass.ASSET)
        income = self.create_ledger_account("salary", AccountClass.INCOME)
        self.post_two_sided("event", cash, income)
        with self.assertRaises(IdempotencyConflictError):
            self.service.post_journal(
                taxpayer_id=self.taxpayer_id,
                effective_date=date(2026, 7, 1),
                event_type="changed",
                postings=(
                    PostingInput(cash, Direction.DEBIT, Money.from_decimal("100.00", "PKR")),
                    PostingInput(income, Direction.CREDIT, Money.from_decimal("100.00", "PKR")),
                ),
                provenance_method=ProvenanceMethod.USER_SUPPLIED,
                review_status=ReviewStatus.USER_CONFIRMED,
                idempotency_key="event",
                expected_revision=self.service.ledger_revision,
                actor=self.actor,
            )
        with self.assertRaises(StaleRevisionError):
            self.service.create_tax_year(
                taxpayer_id=self.taxpayer_id,
                label=2027,
                start_date=date(2026, 7, 1),
                end_date=date(2027, 6, 30),
                idempotency_key="year",
                expected_revision=0,
                actor=self.actor,
            )

    def test_unbalanced_journal_is_atomic(self) -> None:
        cash = self.create_ledger_account("cash", AccountClass.ASSET)
        income = self.create_ledger_account("salary", AccountClass.INCOME)
        revision = self.service.ledger_revision
        with self.assertRaises(UnbalancedJournalError):
            self.service.post_journal(
                taxpayer_id=self.taxpayer_id,
                effective_date=date(2026, 7, 1),
                event_type="bad",
                postings=(
                    PostingInput(cash, Direction.DEBIT, Money.from_decimal("100.00", "PKR")),
                    PostingInput(income, Direction.CREDIT, Money.from_decimal("99.00", "PKR")),
                ),
                provenance_method=ProvenanceMethod.USER_SUPPLIED,
                review_status=ReviewStatus.ACCEPTED,
                idempotency_key="bad",
                expected_revision=revision,
                actor=self.actor,
            )
        self.assertEqual(self.service.ledger_revision, revision)
        self.assertEqual(self.service.operational_status()["journal_entries"], 0)

    def test_document_hash_evidence_and_immutability(self) -> None:
        content = b"deliberately synthetic evidence"
        document = self.service.register_document(
            content=content,
            mime_type="text/plain",
            document_kind="synthetic_certificate",
            idempotency_key="doc-1",
            expected_revision=self.service.ledger_revision,
            actor=self.actor,
        )
        cash = self.create_ledger_account("cash", AccountClass.ASSET)
        income = self.create_ledger_account("salary", AccountClass.INCOME)
        self.service.post_journal(
            taxpayer_id=self.taxpayer_id,
            effective_date=date(2026, 7, 2),
            event_type="salary",
            postings=(
                PostingInput(cash, Direction.DEBIT, Money.from_decimal("100.00", "PKR")),
                PostingInput(income, Direction.CREDIT, Money.from_decimal("100.00", "PKR")),
            ),
            provenance_method=ProvenanceMethod.USER_SUPPLIED,
            review_status=ReviewStatus.VERIFIED,
            idempotency_key="evidenced-event",
            expected_revision=self.service.ledger_revision,
            actor=self.actor,
            evidence=((document, "establishes", "synthetic:1"),),
        )
        with self.service.database.connect() as connection:
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE documents SET document_kind = 'changed' WHERE id = ?", (document,))
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE audit_events SET action = 'changed'")
            with self.assertRaises(sqlite3.IntegrityError):
                connection.execute("UPDATE journal_entries SET event_type = 'changed'")
        self.assertEqual(self.service.database.validate_invariants()["integrity"], "ok")

    def test_correction_reverses_and_replaces_without_mutation(self) -> None:
        cash = self.create_ledger_account("cash", AccountClass.ASSET)
        income = self.create_ledger_account("salary", AccountClass.INCOME)
        original = self.post_two_sided("original", cash, income, "100.00")
        before = self.service.ledger_revision
        result = self.service.correct_journal(
            original_entry_id=original,
            replacement_postings=(
                PostingInput(cash, Direction.DEBIT, Money.from_decimal("120.00", "PKR")),
                PostingInput(income, Direction.CREDIT, Money.from_decimal("120.00", "PKR")),
            ),
            reason="Synthetic amount correction",
            idempotency_key="correct-original",
            expected_revision=before,
            actor=self.actor,
        )
        self.assertEqual(result["ledger_revision"], before + 2)
        repeated = self.service.correct_journal(
            original_entry_id=original,
            replacement_postings=(
                PostingInput(cash, Direction.DEBIT, Money.from_decimal("120.00", "PKR")),
                PostingInput(income, Direction.CREDIT, Money.from_decimal("120.00", "PKR")),
            ),
            reason="Synthetic amount correction",
            idempotency_key="correct-original",
            expected_revision=before,
            actor=self.actor,
        )
        self.assertEqual(repeated, result)
        balances = {row["code"]: row["balance_minor"] for row in self.service.balances(self.taxpayer_id)}
        self.assertEqual(balances["cash"], 12000)
        self.assertEqual(balances["salary"], -12000)
        with self.service.database.connect(readonly=True) as connection:
            count = connection.execute("SELECT COUNT(*) FROM journal_entries").fetchone()[0]
        self.assertEqual(count, 3)

    def test_same_owner_transfer_is_asset_to_asset(self) -> None:
        bank_a = self.service.create_financial_account(
            taxpayer_id=self.taxpayer_id,
            institution="Synthetic Bank A",
            account_kind="current",
            currency="PKR",
            idempotency_key="bank-a",
            expected_revision=self.service.ledger_revision,
            actor=self.actor,
        )
        bank_b = self.service.create_financial_account(
            taxpayer_id=self.taxpayer_id,
            institution="Synthetic Bank B",
            account_kind="savings",
            currency="PKR",
            idempotency_key="bank-b",
            expected_revision=self.service.ledger_revision,
            actor=self.actor,
        )
        for key, account in (("own-a", bank_a), ("own-b", bank_b)):
            self.service.record_account_ownership(
                financial_account_id=account,
                owner_ref=self.taxpayer_id,
                share_numerator=1,
                share_denominator=1,
                effective_from=date(2026, 7, 1),
                effective_to=None,
                review_status=ReviewStatus.VERIFIED,
                idempotency_key=key,
                expected_revision=self.service.ledger_revision,
                actor=self.actor,
            )
        asset_a = self.create_ledger_account("bank-a", AccountClass.ASSET, bank_a)
        asset_b = self.create_ledger_account("bank-b", AccountClass.ASSET, bank_b)
        self.service.post_journal(
            taxpayer_id=self.taxpayer_id,
            effective_date=date(2026, 8, 1),
            event_type="internal_transfer",
            postings=(
                PostingInput(asset_b, Direction.DEBIT, Money.from_decimal("100.00", "PKR")),
                PostingInput(asset_a, Direction.CREDIT, Money.from_decimal("100.00", "PKR")),
            ),
            provenance_method=ProvenanceMethod.RULE_DERIVED,
            review_status=ReviewStatus.VERIFIED,
            idempotency_key="transfer",
            expected_revision=self.service.ledger_revision,
            actor=self.actor,
        )
        with self.service.database.connect(readonly=True) as connection:
            classes = {
                row[0]
                for row in connection.execute(
                    "SELECT DISTINCT a.account_class FROM postings p JOIN ledger_accounts a ON a.id = p.ledger_account_id"
                )
            }
        self.assertEqual(classes, {"asset"})

    def test_overlapping_ownership_cannot_exceed_full_share(self) -> None:
        account = self.service.create_financial_account(
            taxpayer_id=self.taxpayer_id,
            institution="Synthetic Joint Bank",
            account_kind="joint",
            currency="PKR",
            idempotency_key="joint-bank",
            expected_revision=self.service.ledger_revision,
            actor=self.actor,
        )
        self.service.record_account_ownership(
            financial_account_id=account,
            owner_ref="synthetic-owner-a",
            share_numerator=3,
            share_denominator=4,
            effective_from=date(2026, 7, 1),
            effective_to=None,
            review_status=ReviewStatus.USER_CONFIRMED,
            idempotency_key="owner-a",
            expected_revision=self.service.ledger_revision,
            actor=self.actor,
        )
        revision = self.service.ledger_revision
        with self.assertRaises(ValidationError):
            self.service.record_account_ownership(
                financial_account_id=account,
                owner_ref="synthetic-owner-b",
                share_numerator=1,
                share_denominator=2,
                effective_from=date(2026, 8, 1),
                effective_to=None,
                review_status=ReviewStatus.USER_CONFIRMED,
                idempotency_key="owner-b",
                expected_revision=revision,
                actor=self.actor,
            )
        self.assertEqual(self.service.ledger_revision, revision)

    def test_income_expense_loan_and_asset_exchange_keep_distinct_semantics(self) -> None:
        cash = self.create_ledger_account("cash", AccountClass.ASSET)
        property_asset = self.create_ledger_account("property", AccountClass.ASSET)
        loan = self.create_ledger_account("loan", AccountClass.LIABILITY)
        salary = self.create_ledger_account("salary", AccountClass.INCOME)
        living = self.create_ledger_account("living", AccountClass.EXPENSE)
        scenarios = (
            ("salary", cash, Direction.DEBIT, salary, Direction.CREDIT, "500.00"),
            ("living-expense", living, Direction.DEBIT, cash, Direction.CREDIT, "100.00"),
            ("loan-drawdown", cash, Direction.DEBIT, loan, Direction.CREDIT, "1000.00"),
            ("asset-purchase", property_asset, Direction.DEBIT, cash, Direction.CREDIT, "800.00"),
        )
        for key, first, first_direction, second, second_direction, amount in scenarios:
            money = Money.from_decimal(amount, "PKR")
            self.service.post_journal(
                taxpayer_id=self.taxpayer_id,
                effective_date=date(2026, 9, 1),
                event_type=key,
                postings=(
                    PostingInput(first, first_direction, money),
                    PostingInput(second, second_direction, money),
                ),
                provenance_method=ProvenanceMethod.USER_SUPPLIED,
                review_status=ReviewStatus.USER_CONFIRMED,
                idempotency_key=key,
                expected_revision=self.service.ledger_revision,
                actor=self.actor,
            )
        balances = {row["code"]: row["balance_minor"] for row in self.service.balances(self.taxpayer_id)}
        self.assertEqual(balances["cash"], 60000)
        self.assertEqual(balances["property"], 80000)
        self.assertEqual(balances["loan"], -100000)
        self.assertEqual(balances["salary"], -50000)
        self.assertEqual(balances["living"], 10000)

    def test_foreign_currency_requires_and_preserves_pkr_functional_amount(self) -> None:
        foreign_cash = self.service.create_ledger_account(
            taxpayer_id=self.taxpayer_id,
            code="usd-cash",
            name="Synthetic USD cash",
            account_class=AccountClass.ASSET,
            currency_policy="USD",
            idempotency_key="usd-cash",
            expected_revision=self.service.ledger_revision,
            actor=self.actor,
        )
        income = self.create_ledger_account(
            "foreign-income", AccountClass.INCOME, currency_policy="USD"
        )
        usd = Money.from_decimal("100.00", "USD")
        with self.assertRaises(ValidationError):
            self.service.post_journal(
                taxpayer_id=self.taxpayer_id,
                effective_date=date(2026, 10, 1),
                event_type="foreign-receipt",
                postings=(
                    PostingInput(foreign_cash, Direction.DEBIT, usd),
                    PostingInput(income, Direction.CREDIT, usd),
                ),
                provenance_method=ProvenanceMethod.USER_SUPPLIED,
                review_status=ReviewStatus.ACCEPTED,
                idempotency_key="foreign-missing-fx",
                expected_revision=self.service.ledger_revision,
                actor=self.actor,
            )
        self.service.post_journal(
            taxpayer_id=self.taxpayer_id,
            effective_date=date(2026, 10, 1),
            event_type="foreign-receipt",
            postings=(
                PostingInput(foreign_cash, Direction.DEBIT, usd, functional_minor=2_800_000),
                PostingInput(income, Direction.CREDIT, usd, functional_minor=2_800_000),
            ),
            provenance_method=ProvenanceMethod.USER_SUPPLIED,
            review_status=ReviewStatus.ACCEPTED,
            idempotency_key="foreign-with-fx",
            expected_revision=self.service.ledger_revision,
            actor=self.actor,
        )
        with self.service.database.connect(readonly=True) as connection:
            row = connection.execute(
                "SELECT currency, amount_minor, functional_minor FROM postings WHERE ledger_account_id = ?",
                (foreign_cash,),
            ).fetchone()
        self.assertEqual(tuple(row), ("USD", 10000, 2_800_000))


if __name__ == "__main__":
    unittest.main()
