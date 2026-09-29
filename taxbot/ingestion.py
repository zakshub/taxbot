"""Phase 2 statement staging and atomic observation publication.

Adapters produce :class:`StatementExtraction` values.  This service deliberately
does not classify transactions or create journal entries.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any, Sequence

from .database import Database
from .errors import (
    IdempotencyConflictError,
    NotFoundError,
    StaleRevisionError,
    ValidationError,
)
from .util import canonical_json, new_id, request_hash, utc_now


@dataclass(frozen=True, slots=True)
class StatementObservation:
    source_locator: str
    transaction_date: date | None
    narration: str
    direction: str
    amount_minor: int | None
    running_balance_minor: int | None
    raw_fields: dict[str, Any]
    normalized_fields: dict[str, Any]
    value_date: date | None = None
    bank_reference: str | None = None
    extraction_confidence: str = "1"


@dataclass(frozen=True, slots=True)
class StatementExtraction:
    statement_start: date
    statement_end: date
    currency: str
    opening_balance_minor: int | None
    closing_balance_minor: int | None
    declared_debits_minor: int | None
    declared_credits_minor: int | None
    layout_signature: str
    observations: tuple[StatementObservation, ...]
    diagnostics: tuple[str, ...] = ()


class StatementIngestionService:
    """Persist immutable extracted rows, then publish a whole batch atomically."""

    def __init__(self, database: Database) -> None:
        self.database = database

    def stage_extraction(
        self,
        *,
        document_id: str,
        financial_account_id: str,
        adapter_id: str,
        adapter_version: str,
        extractor_id: str,
        extractor_version: str,
        configuration_digest: str,
        run_key: str,
        extraction: StatementExtraction,
        idempotency_key: str,
        expected_revision: int,
        actor: str,
    ) -> dict[str, Any]:
        self._validate_metadata(
            adapter_id,
            adapter_version,
            extractor_id,
            extractor_version,
            configuration_digest,
            run_key,
            extraction,
        )
        diagnostics, actual_debits, actual_credits = self._validate_extraction(extraction)
        extraction_payload = self._extraction_payload(extraction)
        input_digest = request_hash(extraction_payload)
        payload = {
            "document_id": document_id,
            "financial_account_id": financial_account_id,
            "adapter": [adapter_id, adapter_version],
            "extractor": [extractor_id, extractor_version],
            "configuration_digest": configuration_digest,
            "run_key": run_key,
            "extraction": extraction_payload,
            "actor": actor,
        }

        def action(connection: sqlite3.Connection, revision: int) -> dict[str, Any]:
            document = self._require_row(connection, "documents", document_id)
            account = self._require_row(connection, "financial_accounts", financial_account_id)
            if str(document["mime_type"]) != "application/pdf":
                raise ValidationError("The selected Phase 2 adapter requires a PDF document")
            if str(account["currency"]) != extraction.currency.upper():
                raise ValidationError("Statement and financial-account currencies differ")
            existing = connection.execute(
                "SELECT * FROM import_batches WHERE run_key = ?", (run_key,)
            ).fetchone()
            if existing:
                identity = (
                    str(existing["document_id"]),
                    str(existing["financial_account_id"]),
                    str(existing["adapter_id"]),
                    str(existing["adapter_version"]),
                    str(existing["extractor_id"]),
                    str(existing["extractor_version"]),
                    str(existing["configuration_digest"]),
                    str(existing["input_digest"]),
                )
                requested = (
                    document_id,
                    financial_account_id,
                    adapter_id,
                    adapter_version,
                    extractor_id,
                    extractor_version,
                    configuration_digest,
                    input_digest,
                )
                if identity != requested:
                    raise ValidationError("Import run key conflicts with another extraction")
                count = int(
                    connection.execute(
                        "SELECT COUNT(*) FROM source_observations WHERE batch_id = ?",
                        (existing["id"],),
                    ).fetchone()[0]
                )
                return {
                    "batch_id": str(existing["id"]),
                    "state": str(existing["state"]),
                    "diagnostics": (
                        [str(existing["diagnostic_code"])]
                        if existing["diagnostic_code"]
                        else []
                    ),
                    "observation_count": count,
                    "ledger_revision": revision - 1,
                    "reused": True,
                    "_advance_revision": False,
                }
            batch_id = new_id()
            run_id = new_id()
            now = utc_now()
            final_state = "quarantined" if diagnostics else "ready"
            control_status = "failed" if diagnostics else "passed"
            diagnostic_code = diagnostics[0] if diagnostics else None
            connection.execute(
                """
                INSERT INTO import_batches (
                    id, document_id, financial_account_id, adapter_id, adapter_version,
                    extractor_id, extractor_version, configuration_digest, run_key,
                    input_digest, state,
                    statement_start, statement_end, currency, opening_balance_minor,
                    closing_balance_minor, total_debits_minor, total_credits_minor,
                    control_status, layout_signature, diagnostic_code, revision,
                    created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?
                )
                """,
                (
                    batch_id,
                    document_id,
                    financial_account_id,
                    adapter_id,
                    adapter_version,
                    extractor_id,
                    extractor_version,
                    configuration_digest,
                    run_key,
                    input_digest,
                    final_state,
                    extraction.statement_start.isoformat(),
                    extraction.statement_end.isoformat(),
                    extraction.currency.upper(),
                    extraction.opening_balance_minor,
                    extraction.closing_balance_minor,
                    actual_debits,
                    actual_credits,
                    control_status,
                    extraction.layout_signature,
                    diagnostic_code,
                    now,
                    now,
                ),
            )
            checkpoint_states = ["received", "extracting", "normalized"]
            checkpoint_states.append("quarantined" if diagnostics else "validated")
            if not diagnostics:
                checkpoint_states.append("ready")
            for state in checkpoint_states:
                connection.execute(
                    "INSERT INTO import_batch_checkpoints(id, batch_id, state, diagnostic_code, created_at) VALUES (?, ?, ?, ?, ?)",
                    (new_id(), batch_id, state, diagnostic_code if state == "quarantined" else None, now),
                )
            connection.execute(
                "INSERT INTO extraction_runs VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    batch_id,
                    document_id,
                    extractor_id,
                    extractor_version,
                    configuration_digest,
                    "quarantined" if diagnostics else "succeeded",
                    now,
                ),
            )
            for ordinal, observation in enumerate(extraction.observations):
                fingerprint = self._fingerprint(financial_account_id, extraction.currency, observation)
                connection.execute(
                    """
                    INSERT INTO source_observations VALUES (
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        new_id(),
                        batch_id,
                        run_id,
                        document_id,
                        observation.source_locator,
                        ordinal,
                        canonical_json(observation.raw_fields),
                        canonical_json(observation.normalized_fields),
                        observation.transaction_date.isoformat()
                        if observation.transaction_date
                        else None,
                        observation.value_date.isoformat() if observation.value_date else None,
                        observation.narration,
                        observation.bank_reference,
                        observation.direction
                        if observation.direction in {"debit", "credit"}
                        else "unknown",
                        observation.amount_minor,
                        observation.running_balance_minor,
                        extraction.currency.upper(),
                        self._normalized_confidence(observation.extraction_confidence),
                        fingerprint,
                        now,
                    ),
                )
            self._audit(
                connection,
                actor,
                "stage",
                "import_batch",
                batch_id,
                None,
                revision,
                diagnostic_code,
            )
            return {
                "batch_id": batch_id,
                "state": final_state,
                "diagnostics": diagnostics,
                "observation_count": len(extraction.observations),
                "ledger_revision": revision,
                "reused": False,
            }

        return self._run_command(
            "stage_statement_extraction",
            idempotency_key,
            expected_revision,
            payload,
            action,
        )

    def publish_batch(
        self,
        *,
        batch_id: str,
        idempotency_key: str,
        expected_revision: int,
        actor: str,
    ) -> dict[str, Any]:
        payload = {"batch_id": batch_id, "actor": actor}

        def action(connection: sqlite3.Connection, revision: int) -> dict[str, Any]:
            batch = self._require_row(connection, "import_batches", batch_id)
            if str(batch["state"]) != "ready":
                raise ValidationError("Only a ready import batch can be published")
            observations = connection.execute(
                "SELECT * FROM source_observations WHERE batch_id = ? ORDER BY ordinal",
                (batch_id,),
            ).fetchall()
            if not observations:
                raise ValidationError("An empty import batch cannot be published")
            now = utc_now()
            for observation in observations:
                connection.execute(
                    "INSERT INTO published_observations VALUES (?, ?, ?)",
                    (observation["id"], batch_id, now),
                )
            candidate_ids = self._create_duplicate_candidates(
                connection, batch_id, str(batch["financial_account_id"]), now
            )
            assurance = (
                "controlled"
                if batch["opening_balance_minor"] is not None
                and batch["closing_balance_minor"] is not None
                else "partial"
            )
            connection.execute(
                "INSERT INTO statement_coverage VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    new_id(),
                    batch_id,
                    batch["financial_account_id"],
                    batch["statement_start"],
                    batch["statement_end"],
                    assurance,
                    now,
                ),
            )
            connection.execute(
                "UPDATE import_batches SET state = 'accepted', revision = revision + 1, updated_at = ? WHERE id = ?",
                (now, batch_id),
            )
            connection.execute(
                "INSERT INTO import_batch_checkpoints(id, batch_id, state, diagnostic_code, created_at) VALUES (?, ?, 'accepted', NULL, ?)",
                (new_id(), batch_id, now),
            )
            self._audit(
                connection, actor, "publish", "import_batch", batch_id, 1, revision, None
            )
            return {
                "batch_id": batch_id,
                "state": "accepted",
                "published_count": len(observations),
                "duplicate_candidate_count": len(candidate_ids),
                "ledger_revision": revision,
            }

        return self._run_command(
            "publish_statement_batch",
            idempotency_key,
            expected_revision,
            payload,
            action,
        )

    def batch_status(self, batch_id: str) -> dict[str, Any]:
        with self.database.connect(readonly=True) as connection:
            batch = self._require_row(connection, "import_batches", batch_id)
            checkpoints = connection.execute(
                "SELECT state, diagnostic_code, created_at FROM import_batch_checkpoints WHERE batch_id = ? ORDER BY sequence",
                (batch_id,),
            ).fetchall()
            observation_count = int(
                connection.execute(
                    "SELECT COUNT(*) FROM source_observations WHERE batch_id = ?", (batch_id,)
                ).fetchone()[0]
            )
        return {
            "batch_id": batch_id,
            "state": str(batch["state"]),
            "control_status": str(batch["control_status"]),
            "diagnostic_code": batch["diagnostic_code"],
            "observation_count": observation_count,
            "checkpoints": [dict(row) for row in checkpoints],
        }

    @staticmethod
    def _validate_metadata(
        adapter_id: str,
        adapter_version: str,
        extractor_id: str,
        extractor_version: str,
        configuration_digest: str,
        run_key: str,
        extraction: StatementExtraction,
    ) -> None:
        if not all(
            value.strip()
            for value in (
                adapter_id,
                adapter_version,
                extractor_id,
                extractor_version,
                run_key,
                extraction.layout_signature,
            )
        ):
            raise ValidationError("Adapter, extractor, run and layout identifiers are required")
        if len(configuration_digest) != 64 or any(
            character not in "0123456789abcdef" for character in configuration_digest.lower()
        ):
            raise ValidationError("Configuration digest must be a SHA-256 hex digest")
        if extraction.statement_start > extraction.statement_end:
            raise ValidationError("Statement start must not follow statement end")
        if extraction.currency.upper() != "PKR":
            raise ValidationError("The first statement adapter supports PKR only")

    @classmethod
    def _validate_extraction(
        cls, extraction: StatementExtraction
    ) -> tuple[list[str], int, int]:
        diagnostics: list[str] = []
        for diagnostic in extraction.diagnostics:
            if not diagnostic or any(
                character not in "abcdefghijklmnopqrstuvwxyz0123456789_" for character in diagnostic
            ):
                raise ValidationError("Adapter diagnostic codes must be lowercase identifiers")
            diagnostics.append(diagnostic)
        if not extraction.observations:
            diagnostics.append("empty_statement")
        seen_locators: set[str] = set()
        actual_debits = 0
        actual_credits = 0
        expected_balance = extraction.opening_balance_minor
        for observation in extraction.observations:
            if not observation.source_locator.strip() or observation.source_locator in seen_locators:
                diagnostics.append("invalid_source_locator")
            seen_locators.add(observation.source_locator)
            if observation.direction not in {"debit", "credit"}:
                diagnostics.append("ambiguous_direction")
            valid_amount = (
                type(observation.amount_minor) is int and observation.amount_minor > 0
            )
            if not valid_amount:
                diagnostics.append("invalid_amount")
            if observation.transaction_date is None:
                diagnostics.append("missing_transaction_date")
            elif not extraction.statement_start <= observation.transaction_date <= extraction.statement_end:
                diagnostics.append("transaction_outside_statement_period")
            try:
                cls._normalized_confidence(observation.extraction_confidence)
            except ValidationError:
                diagnostics.append("invalid_extraction_confidence")
            if observation.direction == "debit" and valid_amount:
                actual_debits += observation.amount_minor
                if expected_balance is not None:
                    expected_balance -= observation.amount_minor
            elif observation.direction == "credit" and valid_amount:
                actual_credits += observation.amount_minor
                if expected_balance is not None:
                    expected_balance += observation.amount_minor
            if (
                expected_balance is not None
                and observation.running_balance_minor is not None
                and observation.running_balance_minor != expected_balance
            ):
                diagnostics.append("running_balance_mismatch")
        if (
            extraction.declared_debits_minor is not None
            and extraction.declared_debits_minor != actual_debits
        ):
            diagnostics.append("debit_total_mismatch")
        if (
            extraction.declared_credits_minor is not None
            and extraction.declared_credits_minor != actual_credits
        ):
            diagnostics.append("credit_total_mismatch")
        if (
            extraction.opening_balance_minor is not None
            and extraction.closing_balance_minor is not None
            and extraction.opening_balance_minor + actual_credits - actual_debits
            != extraction.closing_balance_minor
        ):
            diagnostics.append("closing_balance_mismatch")
        if expected_balance is not None and extraction.closing_balance_minor is not None:
            if expected_balance != extraction.closing_balance_minor:
                diagnostics.append("running_control_mismatch")
        return list(dict.fromkeys(diagnostics)), actual_debits, actual_credits

    @staticmethod
    def _normalized_confidence(value: str) -> str:
        try:
            confidence = Decimal(value)
        except (InvalidOperation, TypeError) as exc:
            raise ValidationError("Extraction confidence must be an exact decimal") from exc
        if not confidence.is_finite():
            raise ValidationError("Extraction confidence must be finite")
        if not Decimal("0") <= confidence <= Decimal("1"):
            raise ValidationError("Extraction confidence must be between zero and one")
        return format(confidence.normalize(), "f")

    @staticmethod
    def _fingerprint(
        financial_account_id: str, currency: str, observation: StatementObservation
    ) -> str:
        return request_hash(
            {
                "financial_account_id": financial_account_id,
                "currency": currency.upper(),
                "transaction_date": observation.transaction_date.isoformat()
                if observation.transaction_date
                else None,
                "value_date": observation.value_date.isoformat() if observation.value_date else None,
                "direction": observation.direction,
                "amount_minor": observation.amount_minor,
                "narration": " ".join(observation.narration.upper().split()),
                "bank_reference": observation.bank_reference,
                "running_balance_minor": observation.running_balance_minor,
            }
        )

    def _create_duplicate_candidates(
        self,
        connection: sqlite3.Connection,
        batch_id: str,
        financial_account_id: str,
        now: str,
    ) -> list[str]:
        current = connection.execute(
            "SELECT * FROM source_observations WHERE batch_id = ?", (batch_id,)
        ).fetchall()
        candidates: list[str] = []
        for observation in current:
            matches = connection.execute(
                """
                SELECT o.*
                FROM source_observations o
                JOIN import_batches b ON b.id = o.batch_id
                JOIN published_observations p ON p.observation_id = o.id
                WHERE b.financial_account_id = ? AND o.id != ?
                  AND (o.contextual_fingerprint = ? OR
                       (? IS NOT NULL AND o.bank_reference = ?))
                """,
                (
                    financial_account_id,
                    observation["id"],
                    observation["contextual_fingerprint"],
                    observation["bank_reference"],
                    observation["bank_reference"],
                ),
            ).fetchall()
            for match in matches:
                left, right = sorted((str(observation["id"]), str(match["id"])))
                kinds: list[str] = []
                if observation["contextual_fingerprint"] == match["contextual_fingerprint"]:
                    kinds.append("overlap_fingerprint")
                if observation["bank_reference"] and observation["bank_reference"] == match["bank_reference"]:
                    kinds.append("bank_reference")
                for kind in kinds:
                    candidate_id = new_id()
                    cursor = connection.execute(
                        """
                        INSERT OR IGNORE INTO duplicate_candidates
                            (id, left_observation_id, right_observation_id, candidate_kind, reason_json, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            candidate_id,
                            left,
                            right,
                            kind,
                            canonical_json({"kind": kind, "decision": "review_required"}),
                            now,
                        ),
                    )
                    if cursor.rowcount:
                        candidates.append(candidate_id)
        return candidates

    @staticmethod
    def _extraction_payload(extraction: StatementExtraction) -> dict[str, Any]:
        return {
            "statement_start": extraction.statement_start.isoformat(),
            "statement_end": extraction.statement_end.isoformat(),
            "currency": extraction.currency.upper(),
            "opening_balance_minor": extraction.opening_balance_minor,
            "closing_balance_minor": extraction.closing_balance_minor,
            "declared_debits_minor": extraction.declared_debits_minor,
            "declared_credits_minor": extraction.declared_credits_minor,
            "layout_signature": extraction.layout_signature,
            "diagnostics": list(extraction.diagnostics),
            "observations": [
                {
                    "source_locator": item.source_locator,
                    "transaction_date": item.transaction_date.isoformat()
                    if item.transaction_date
                    else None,
                    "value_date": item.value_date.isoformat() if item.value_date else None,
                    "narration": item.narration,
                    "bank_reference": item.bank_reference,
                    "direction": item.direction,
                    "amount_minor": item.amount_minor,
                    "running_balance_minor": item.running_balance_minor,
                    "raw_fields": item.raw_fields,
                    "normalized_fields": item.normalized_fields,
                    "extraction_confidence": item.extraction_confidence,
                }
                for item in extraction.observations
            ],
        }

    def _run_command(
        self,
        command_type: str,
        key: str,
        expected_revision: int,
        payload: dict[str, Any],
        action: Any,
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
                    raise IdempotencyConflictError(
                        "Idempotency key was reused with another request"
                    )
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
            advance_revision = bool(result.pop("_advance_revision", True))
            if advance_revision:
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

    @staticmethod
    def _require_row(
        connection: sqlite3.Connection, table: str, identifier: str
    ) -> sqlite3.Row:
        allowed = {"documents", "financial_accounts", "import_batches"}
        if table not in allowed:
            raise ValueError("Unsupported lookup table")
        row = connection.execute(f"SELECT * FROM {table} WHERE id = ?", (identifier,)).fetchone()
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
        after_revision: int,
        reason: str | None,
    ) -> None:
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
