"""Atomic, idempotent Phase 1 ledger commands."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable, Sequence
from datetime import date
from fractions import Fraction
from pathlib import Path
from typing import Any

from .database import Database
from .documents import DocumentStore
from .errors import (
    IdempotencyConflictError,
    NotFoundError,
    StaleRevisionError,
    UnbalancedJournalError,
    ValidationError,
)
from .models import AccountClass, Direction, PostingInput, ProvenanceMethod, ReviewStatus
from .money import Money
from .storage import StoragePolicy
from .util import canonical_json, new_id, request_hash, utc_now


class LedgerService:
    def __init__(self, policy: StoragePolicy) -> None:
        self.policy = policy
        policy.prepare_directories()
        self.database = Database(policy.database_path)
        self.database.migrate()
        self.documents = DocumentStore(policy.objects_root)

    @staticmethod
    def setup_empty_store(policy: StoragePolicy) -> dict[str, int | str]:
        """Create an empty schema; real mode still cannot accept data before restore proof."""
        policy.prepare_directories(setup_only=True)
        database = Database(policy.database_path)
        database.migrate()
        return database.validate_invariants()

    @property
    def ledger_revision(self) -> int:
        return self.database.ledger_revision()

    def create_taxpayer(
        self,
        *,
        residency_status: str,
        idempotency_key: str,
        expected_revision: int,
        actor: str,
        private_identifier_ref: str | None = None,
    ) -> str:
        payload = {
            "residency_status": residency_status,
            "private_identifier_ref": private_identifier_ref,
            "actor": actor,
        }
        if residency_status not in {"resident", "nonresident", "unknown"}:
            raise ValidationError("Unsupported residency status")

        def action(connection: sqlite3.Connection, revision: int) -> dict[str, Any]:
            if connection.execute("SELECT 1 FROM taxpayer_profiles LIMIT 1").fetchone():
                raise ValidationError("Phase 1 supports one taxpayer profile")
            taxpayer_id = new_id()
            now = utc_now()
            connection.execute(
                "INSERT INTO taxpayer_profiles VALUES (?, 1, ?, ?, ?)",
                (taxpayer_id, residency_status, private_identifier_ref, now),
            )
            self._audit(connection, actor, "create", "taxpayer_profile", taxpayer_id, None, 1)
            return {"taxpayer_id": taxpayer_id, "ledger_revision": revision}

        return str(
            self._run_command(
                "create_taxpayer", idempotency_key, expected_revision, payload, action
            )["taxpayer_id"]
        )

    def create_tax_year(
        self,
        *,
        taxpayer_id: str,
        label: int,
        start_date: date,
        end_date: date,
        idempotency_key: str,
        expected_revision: int,
        actor: str,
    ) -> str:
        if start_date > end_date:
            raise ValidationError("Tax-year start must not follow end")
        payload = {
            "taxpayer_id": taxpayer_id,
            "label": label,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "actor": actor,
        }

        def action(connection: sqlite3.Connection, revision: int) -> dict[str, Any]:
            self._require_row(connection, "taxpayer_profiles", taxpayer_id)
            overlap = connection.execute(
                """
                SELECT 1 FROM tax_years
                WHERE taxpayer_id = ? AND NOT (end_date < ? OR start_date > ?)
                """,
                (taxpayer_id, start_date.isoformat(), end_date.isoformat()),
            ).fetchone()
            if overlap:
                raise ValidationError("Tax-year periods must not overlap")
            tax_year_id = new_id()
            connection.execute(
                "INSERT INTO tax_years VALUES (?, ?, ?, ?, ?, 'open', ?)",
                (
                    tax_year_id,
                    taxpayer_id,
                    label,
                    start_date.isoformat(),
                    end_date.isoformat(),
                    utc_now(),
                ),
            )
            self._audit(connection, actor, "create", "tax_year", tax_year_id, None, 1)
            return {"tax_year_id": tax_year_id, "ledger_revision": revision}

        return str(
            self._run_command(
                "create_tax_year", idempotency_key, expected_revision, payload, action
            )["tax_year_id"]
        )

    def create_financial_account(
        self,
        *,
        taxpayer_id: str,
        institution: str,
        account_kind: str,
        currency: str,
        idempotency_key: str,
        expected_revision: int,
        actor: str,
        private_identifier_ref: str | None = None,
    ) -> str:
        normalized_currency = currency.upper()
        if normalized_currency not in Money.SCALES:
            raise ValidationError("Unsupported account currency")
        if not institution.strip() or not account_kind.strip():
            raise ValidationError("Institution and account kind are required")
        payload = {
            "taxpayer_id": taxpayer_id,
            "institution": institution,
            "account_kind": account_kind,
            "currency": normalized_currency,
            "private_identifier_ref": private_identifier_ref,
            "actor": actor,
        }

        def action(connection: sqlite3.Connection, revision: int) -> dict[str, Any]:
            self._require_row(connection, "taxpayer_profiles", taxpayer_id)
            account_id = new_id()
            connection.execute(
                "INSERT INTO financial_accounts VALUES (?, ?, ?, ?, ?, ?, 'active', 1, ?)",
                (
                    account_id,
                    taxpayer_id,
                    institution,
                    account_kind,
                    normalized_currency,
                    private_identifier_ref,
                    utc_now(),
                ),
            )
            self._audit(connection, actor, "create", "financial_account", account_id, None, 1)
            return {"financial_account_id": account_id, "ledger_revision": revision}

        return str(
            self._run_command(
                "create_financial_account", idempotency_key, expected_revision, payload, action
            )["financial_account_id"]
        )

    def record_account_ownership(
        self,
        *,
        financial_account_id: str,
        owner_ref: str,
        share_numerator: int,
        share_denominator: int,
        effective_from: date,
        effective_to: date | None,
        review_status: ReviewStatus,
        idempotency_key: str,
        expected_revision: int,
        actor: str,
        evidence_document_id: str | None = None,
    ) -> str:
        if share_numerator <= 0 or share_denominator <= 0 or share_numerator > share_denominator:
            raise ValidationError("Ownership share is invalid")
        if effective_to and effective_to < effective_from:
            raise ValidationError("Ownership end precedes start")
        payload = {
            "financial_account_id": financial_account_id,
            "owner_ref": owner_ref,
            "share": [share_numerator, share_denominator],
            "effective_from": effective_from.isoformat(),
            "effective_to": effective_to.isoformat() if effective_to else None,
            "review_status": review_status.value,
            "evidence_document_id": evidence_document_id,
            "actor": actor,
        }

        def action(connection: sqlite3.Connection, revision: int) -> dict[str, Any]:
            self._require_row(connection, "financial_accounts", financial_account_id)
            if evidence_document_id:
                self._require_row(connection, "documents", evidence_document_id)
            overlapping = connection.execute(
                """
                SELECT owner_ref, share_numerator, share_denominator, effective_from, effective_to
                FROM account_ownership
                WHERE financial_account_id = ?
                  AND NOT (COALESCE(effective_to, '9999-12-31') < ? OR effective_from > ?)
                """,
                (
                    financial_account_id,
                    effective_from.isoformat(),
                    effective_to.isoformat() if effective_to else "9999-12-31",
                ),
            ).fetchall()
            if any(row["owner_ref"] == owner_ref for row in overlapping):
                raise ValidationError("Overlapping ownership periods for the same owner are not allowed")
            checkpoints = {effective_from}
            if effective_to:
                checkpoints.add(effective_to)
            for row in overlapping:
                row_start = date.fromisoformat(str(row["effective_from"]))
                row_end = (
                    date.fromisoformat(str(row["effective_to"]))
                    if row["effective_to"]
                    else None
                )
                checkpoints.add(max(effective_from, row_start))
                if effective_to and row_end:
                    checkpoints.add(min(effective_to, row_end))
            new_share = Fraction(share_numerator, share_denominator)
            for checkpoint in checkpoints:
                total = new_share
                for row in overlapping:
                    row_start = date.fromisoformat(str(row["effective_from"]))
                    row_end = (
                        date.fromisoformat(str(row["effective_to"]))
                        if row["effective_to"]
                        else None
                    )
                    if row_start <= checkpoint and (row_end is None or checkpoint <= row_end):
                        total += Fraction(int(row["share_numerator"]), int(row["share_denominator"]))
                if total > 1:
                    raise ValidationError("Overlapping ownership shares exceed 100 percent")
            ownership_id = new_id()
            connection.execute(
                "INSERT INTO account_ownership VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)",
                (
                    ownership_id,
                    financial_account_id,
                    owner_ref,
                    share_numerator,
                    share_denominator,
                    effective_from.isoformat(),
                    effective_to.isoformat() if effective_to else None,
                    evidence_document_id,
                    review_status.value,
                    utc_now(),
                ),
            )
            self._audit(connection, actor, "create", "account_ownership", ownership_id, None, 1)
            return {"ownership_id": ownership_id, "ledger_revision": revision}

        return str(
            self._run_command(
                "record_account_ownership", idempotency_key, expected_revision, payload, action
            )["ownership_id"]
        )

    def create_ledger_account(
        self,
        *,
        taxpayer_id: str,
        code: str,
        name: str,
        account_class: AccountClass,
        currency_policy: str,
        idempotency_key: str,
        expected_revision: int,
        actor: str,
        financial_account_id: str | None = None,
    ) -> str:
        normalized_policy = currency_policy.upper()
        if not code.strip() or not name.strip() or not normalized_policy:
            raise ValidationError("Ledger account code, name and currency policy are required")
        if normalized_policy != "MULTI" and normalized_policy not in Money.SCALES:
            raise ValidationError("Unsupported ledger currency policy")
        payload = {
            "taxpayer_id": taxpayer_id,
            "code": code,
            "name": name,
            "account_class": account_class.value,
            "currency_policy": normalized_policy,
            "financial_account_id": financial_account_id,
            "actor": actor,
        }

        def action(connection: sqlite3.Connection, revision: int) -> dict[str, Any]:
            self._require_row(connection, "taxpayer_profiles", taxpayer_id)
            if financial_account_id:
                row = self._require_row(connection, "financial_accounts", financial_account_id)
                if row["taxpayer_id"] != taxpayer_id:
                    raise ValidationError("Financial and ledger accounts have different taxpayers")
                if normalized_policy != row["currency"]:
                    raise ValidationError("Linked financial and ledger account currencies differ")
            account_id = new_id()
            connection.execute(
                "INSERT INTO ledger_accounts VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)",
                (
                    account_id,
                    taxpayer_id,
                    code,
                    name,
                    account_class.value,
                    normalized_policy,
                    financial_account_id,
                    utc_now(),
                ),
            )
            self._audit(connection, actor, "create", "ledger_account", account_id, None, 1)
            return {"ledger_account_id": account_id, "ledger_revision": revision}

        return str(
            self._run_command(
                "create_ledger_account", idempotency_key, expected_revision, payload, action
            )["ledger_account_id"]
        )

    def register_document(
        self,
        *,
        content: bytes,
        mime_type: str,
        document_kind: str,
        idempotency_key: str,
        expected_revision: int,
        actor: str,
    ) -> str:
        if not mime_type or not document_kind:
            raise ValidationError("Document MIME type and kind are required")
        digest, relative_path = self.documents.put(content)
        payload = {
            "sha256": digest,
            "byte_length": len(content),
            "mime_type": mime_type,
            "document_kind": document_kind,
            "actor": actor,
        }

        def action(connection: sqlite3.Connection, revision: int) -> dict[str, Any]:
            existing = connection.execute(
                "SELECT id FROM documents WHERE sha256 = ?", (digest,)
            ).fetchone()
            if existing:
                document_id = str(existing["id"])
            else:
                document_id = new_id()
                now = utc_now()
                connection.execute(
                    "INSERT INTO documents VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (
                        document_id,
                        digest,
                        relative_path,
                        mime_type,
                        len(content),
                        document_kind,
                        now,
                        now,
                    ),
                )
            self._audit(connection, actor, "register", "document", document_id, None, 1)
            return {"document_id": document_id, "ledger_revision": revision}

        return str(
            self._run_command(
                "register_document", idempotency_key, expected_revision, payload, action
            )["document_id"]
        )

    def post_journal(
        self,
        *,
        taxpayer_id: str,
        effective_date: date,
        event_type: str,
        postings: Sequence[PostingInput],
        provenance_method: ProvenanceMethod,
        review_status: ReviewStatus,
        idempotency_key: str,
        expected_revision: int,
        actor: str,
        description: str | None = None,
        evidence: Sequence[tuple[str, str, str | None]] = (),
    ) -> str:
        normalized = self._normalize_postings(postings)
        payload = self._journal_payload(
            taxpayer_id,
            effective_date,
            event_type,
            normalized,
            provenance_method,
            review_status,
            description,
            evidence,
        )
        payload["actor"] = actor

        def action(connection: sqlite3.Connection, revision: int) -> dict[str, Any]:
            entry_id = self._insert_journal(
                connection,
                taxpayer_id=taxpayer_id,
                effective_date=effective_date,
                event_type=event_type,
                postings=normalized,
                provenance_method=provenance_method,
                review_status=review_status,
                ledger_revision=revision,
                description=description,
                evidence=evidence,
            )
            self._audit(connection, actor, "post", "journal_entry", entry_id, None, revision)
            return {"entry_id": entry_id, "ledger_revision": revision}

        return str(
            self._run_command("post_journal", idempotency_key, expected_revision, payload, action)[
                "entry_id"
            ]
        )

    def correct_journal(
        self,
        *,
        original_entry_id: str,
        replacement_postings: Sequence[PostingInput],
        reason: str,
        idempotency_key: str,
        expected_revision: int,
        actor: str,
        replacement_event_type: str | None = None,
        replacement_description: str | None = None,
        evidence: Sequence[tuple[str, str, str | None]] = (),
    ) -> dict[str, Any]:
        if not idempotency_key.strip():
            raise ValidationError("Idempotency key is required")
        if not reason.strip():
            raise ValidationError("Correction reason is required")
        normalized = self._normalize_postings(replacement_postings)
        payload = {
            "original_entry_id": original_entry_id,
            "replacement_event_type": replacement_event_type,
            "replacement_description": replacement_description,
            "reason": reason,
            "postings": self._postings_payload(normalized),
            "evidence": list(evidence),
            "actor": actor,
        }
        return self._run_correction(
            idempotency_key, expected_revision, payload, actor, normalized, evidence
        )

    def balances(self, taxpayer_id: str) -> list[dict[str, Any]]:
        with self.database.connect(readonly=True) as connection:
            rows = connection.execute(
                """
                SELECT a.id, a.code, a.name, a.account_class,
                    COALESCE(SUM(CASE WHEN p.direction = 'debit' THEN p.functional_minor ELSE -p.functional_minor END), 0) AS balance_minor
                FROM ledger_accounts a
                LEFT JOIN postings p ON p.ledger_account_id = a.id
                WHERE a.taxpayer_id = ?
                GROUP BY a.id, a.code, a.name, a.account_class
                ORDER BY a.code
                """,
                (taxpayer_id,),
            ).fetchall()
        return [dict(row) for row in rows]

    def operational_status(self) -> dict[str, int | str]:
        validation = self.database.validate_invariants()
        with self.database.connect(readonly=True) as connection:
            counts = {
                "taxpayers": connection.execute("SELECT COUNT(*) FROM taxpayer_profiles").fetchone()[0],
                "financial_accounts": connection.execute("SELECT COUNT(*) FROM financial_accounts").fetchone()[0],
                "ledger_accounts": connection.execute("SELECT COUNT(*) FROM ledger_accounts").fetchone()[0],
                "documents": connection.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
                "journal_entries": connection.execute("SELECT COUNT(*) FROM journal_entries").fetchone()[0],
                "audit_events": connection.execute("SELECT COUNT(*) FROM audit_events").fetchone()[0],
            }
        return {**validation, **{key: int(value) for key, value in counts.items()}}

    def _run_command(
        self,
        command_type: str,
        key: str,
        expected_revision: int,
        payload: dict[str, Any],
        action: Callable[[sqlite3.Connection, int], dict[str, Any]],
    ) -> dict[str, Any]:
        if not key.strip():
            raise ValidationError("Idempotency key is required")
        digest = request_hash(payload)
        connection = self.database.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            cached = connection.execute(
                "SELECT command_type, request_hash, result_json FROM idempotency_records WHERE command_key = ?",
                (key,),
            ).fetchone()
            if cached:
                if cached["command_type"] != command_type or cached["request_hash"] != digest:
                    raise IdempotencyConflictError("Idempotency key was reused with another request")
                connection.execute("COMMIT")
                return json.loads(cached["result_json"])
            current = int(
                connection.execute(
                    "SELECT ledger_revision FROM system_state WHERE singleton = 1"
                ).fetchone()[0]
            )
            if current != expected_revision:
                raise StaleRevisionError(
                    f"Expected ledger revision {expected_revision}, current revision is {current}"
                )
            revision = current + 1
            result = action(connection, revision)
            connection.execute(
                "UPDATE system_state SET ledger_revision = ? WHERE singleton = 1", (revision,)
            )
            connection.execute(
                "INSERT INTO idempotency_records VALUES (?, ?, ?, ?, ?)",
                (key, command_type, digest, canonical_json(result), utc_now()),
            )
            connection.execute("COMMIT")
            return result
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def _run_correction(
        self,
        key: str,
        expected_revision: int,
        payload: dict[str, Any],
        actor: str,
        replacement_postings: Sequence[PostingInput],
        evidence: Sequence[tuple[str, str, str | None]],
    ) -> dict[str, Any]:
        digest = request_hash(payload)
        connection = self.database.connect()
        try:
            connection.execute("BEGIN IMMEDIATE")
            cached = connection.execute(
                "SELECT command_type, request_hash, result_json FROM idempotency_records WHERE command_key = ?",
                (key,),
            ).fetchone()
            if cached:
                if cached["command_type"] != "correct_journal" or cached["request_hash"] != digest:
                    raise IdempotencyConflictError("Idempotency key was reused with another request")
                connection.execute("COMMIT")
                return json.loads(cached["result_json"])
            current = int(
                connection.execute(
                    "SELECT ledger_revision FROM system_state WHERE singleton = 1"
                ).fetchone()[0]
            )
            if current != expected_revision:
                raise StaleRevisionError(
                    f"Expected ledger revision {expected_revision}, current revision is {current}"
                )
            original = connection.execute(
                "SELECT * FROM journal_entries WHERE id = ?", (payload["original_entry_id"],)
            ).fetchone()
            if not original:
                raise NotFoundError("Original journal entry not found")
            original_postings = connection.execute(
                "SELECT * FROM postings WHERE journal_entry_id = ? ORDER BY ordinal",
                (payload["original_entry_id"],),
            ).fetchall()
            reversal_postings = [
                PostingInput(
                    ledger_account_id=str(row["ledger_account_id"]),
                    direction=(
                        Direction.CREDIT if row["direction"] == Direction.DEBIT else Direction.DEBIT
                    ),
                    amount=Money.from_minor(int(row["amount_minor"]), str(row["currency"])),
                    functional_minor=int(row["functional_minor"]),
                )
                for row in original_postings
            ]
            reversal_id = self._insert_journal(
                connection,
                taxpayer_id=str(original["taxpayer_id"]),
                effective_date=date.fromisoformat(str(original["effective_date"])),
                event_type="correction_reversal",
                postings=reversal_postings,
                provenance_method=ProvenanceMethod.USER_SUPPLIED,
                review_status=ReviewStatus.USER_CONFIRMED,
                ledger_revision=current + 1,
                description="Correction reversal",
                evidence=(),
                correction_of=str(original["id"]),
                reverses_entry_id=str(original["id"]),
            )
            replacement_id = self._insert_journal(
                connection,
                taxpayer_id=str(original["taxpayer_id"]),
                effective_date=date.fromisoformat(str(original["effective_date"])),
                event_type=payload["replacement_event_type"] or str(original["event_type"]),
                postings=replacement_postings,
                provenance_method=ProvenanceMethod.USER_SUPPLIED,
                review_status=ReviewStatus.USER_CONFIRMED,
                ledger_revision=current + 2,
                description=payload["replacement_description"],
                evidence=evidence,
                correction_of=str(original["id"]),
            )
            self._audit(
                connection,
                actor,
                "reverse_for_correction",
                "journal_entry",
                reversal_id,
                int(original["ledger_revision"]),
                current + 1,
                reason=payload["reason"],
            )
            self._audit(
                connection,
                actor,
                "replace_for_correction",
                "journal_entry",
                replacement_id,
                int(original["ledger_revision"]),
                current + 2,
                reason=payload["reason"],
            )
            result = {
                "reversal_entry_id": reversal_id,
                "replacement_entry_id": replacement_id,
                "ledger_revision": current + 2,
            }
            connection.execute(
                "UPDATE system_state SET ledger_revision = ? WHERE singleton = 1", (current + 2,)
            )
            connection.execute(
                "INSERT INTO idempotency_records VALUES (?, 'correct_journal', ?, ?, ?)",
                (key, digest, canonical_json(result), utc_now()),
            )
            connection.execute("COMMIT")
            return result
        except Exception:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()

    def _insert_journal(
        self,
        connection: sqlite3.Connection,
        *,
        taxpayer_id: str,
        effective_date: date,
        event_type: str,
        postings: Sequence[PostingInput],
        provenance_method: ProvenanceMethod,
        review_status: ReviewStatus,
        ledger_revision: int,
        description: str | None,
        evidence: Sequence[tuple[str, str, str | None]],
        correction_of: str | None = None,
        reverses_entry_id: str | None = None,
    ) -> str:
        self._require_row(connection, "taxpayer_profiles", taxpayer_id)
        if not event_type.strip():
            raise ValidationError("Event type is required")
        account_ids = {posting.ledger_account_id for posting in postings}
        placeholders = ",".join("?" for _ in account_ids)
        rows = connection.execute(
            f"SELECT id, taxpayer_id, currency_policy FROM ledger_accounts WHERE id IN ({placeholders})",
            tuple(account_ids),
        ).fetchall()
        if len(rows) != len(account_ids):
            raise NotFoundError("Ledger account not found")
        if any(row["taxpayer_id"] != taxpayer_id for row in rows):
            raise ValidationError("All postings must belong to the journal taxpayer")
        policies = {str(row["id"]): str(row["currency_policy"]) for row in rows}
        for posting in postings:
            policy = policies[posting.ledger_account_id]
            if policy != "MULTI" and policy != posting.amount.currency:
                raise ValidationError("Posting currency violates ledger account policy")
        for document_id, role, _ in evidence:
            self._require_row(connection, "documents", document_id)
            if role not in {"establishes", "corroborates", "contradicts", "explains_component"}:
                raise ValidationError("Unsupported evidence role")
        entry_id = new_id()
        now = utc_now()
        connection.execute(
            "INSERT INTO journal_entries VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                entry_id,
                taxpayer_id,
                effective_date.isoformat(),
                event_type,
                description,
                provenance_method.value,
                review_status.value,
                ledger_revision,
                correction_of,
                reverses_entry_id,
                now,
            ),
        )
        for ordinal, posting in enumerate(postings):
            connection.execute(
                "INSERT INTO postings VALUES (?, ?, ?, ?, ?, ?, ?, 'PKR', ?)",
                (
                    new_id(),
                    entry_id,
                    posting.ledger_account_id,
                    ordinal,
                    posting.direction.value,
                    posting.amount.currency,
                    posting.amount.minor,
                    posting.resolved_functional_minor(),
                ),
            )
        for document_id, role, locator in evidence:
            connection.execute(
                "INSERT INTO journal_evidence_links VALUES (?, ?, ?, ?, ?, ?)",
                (new_id(), entry_id, document_id, role, locator, now),
            )
        return entry_id

    @staticmethod
    def _normalize_postings(postings: Sequence[PostingInput]) -> tuple[PostingInput, ...]:
        result = tuple(postings)
        if len(result) < 2:
            raise UnbalancedJournalError("A journal requires at least two postings")
        if any(posting.amount.minor <= 0 for posting in result):
            raise ValidationError("Posting amounts must be positive")
        try:
            debits = sum(
                posting.resolved_functional_minor()
                for posting in result
                if posting.direction == Direction.DEBIT
            )
            credits = sum(
                posting.resolved_functional_minor()
                for posting in result
                if posting.direction == Direction.CREDIT
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        if debits <= 0 or debits != credits:
            raise UnbalancedJournalError("Functional PKR debits and credits must balance")
        return result

    @staticmethod
    def _postings_payload(postings: Sequence[PostingInput]) -> list[dict[str, Any]]:
        return [
            {
                "ledger_account_id": posting.ledger_account_id,
                "direction": posting.direction.value,
                "currency": posting.amount.currency,
                "amount_minor": posting.amount.minor,
                "functional_minor": posting.resolved_functional_minor(),
            }
            for posting in postings
        ]

    def _journal_payload(
        self,
        taxpayer_id: str,
        effective_date: date,
        event_type: str,
        postings: Sequence[PostingInput],
        provenance_method: ProvenanceMethod,
        review_status: ReviewStatus,
        description: str | None,
        evidence: Sequence[tuple[str, str, str | None]],
    ) -> dict[str, Any]:
        return {
            "taxpayer_id": taxpayer_id,
            "effective_date": effective_date.isoformat(),
            "event_type": event_type,
            "description": description,
            "provenance_method": provenance_method.value,
            "review_status": review_status.value,
            "postings": self._postings_payload(postings),
            "evidence": list(evidence),
        }

    @staticmethod
    def _require_row(connection: sqlite3.Connection, table: str, item_id: str) -> sqlite3.Row:
        allowed = {
            "taxpayer_profiles",
            "financial_accounts",
            "ledger_accounts",
            "documents",
            "journal_entries",
        }
        if table not in allowed:
            raise ValueError("Unsupported table lookup")
        row = connection.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()
        if not row:
            raise NotFoundError(f"{table} record not found")
        return row

    @staticmethod
    def _audit(
        connection: sqlite3.Connection,
        actor: str,
        action: str,
        target_type: str,
        target_id: str,
        before_revision: int | None,
        after_revision: int | None,
        *,
        reason: str | None = None,
    ) -> None:
        if not actor.strip():
            raise ValidationError("Actor is required")
        connection.execute(
            "INSERT INTO audit_events(id, actor, action, target_type, target_id, before_revision, after_revision, reason, run_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                new_id(),
                actor,
                action,
                target_type,
                target_id,
                before_revision,
                after_revision,
                reason,
                new_id(),
                utc_now(),
            ),
        )
