"""Small immutable command/value types for the Phase 1 domain."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum

from .money import Money


class AccountClass(StrEnum):
    ASSET = "asset"
    LIABILITY = "liability"
    EQUITY = "equity"
    INCOME = "income"
    EXPENSE = "expense"
    CLEARING = "clearing"


class Direction(StrEnum):
    DEBIT = "debit"
    CREDIT = "credit"


class ProvenanceMethod(StrEnum):
    MACHINE_PROPOSED = "machine_proposed"
    RULE_DERIVED = "rule_derived"
    USER_SUPPLIED = "user_supplied"


class ReviewStatus(StrEnum):
    ACCEPTED = "accepted"
    USER_CONFIRMED = "user_confirmed"
    VERIFIED = "verified"


@dataclass(frozen=True, slots=True)
class PostingInput:
    ledger_account_id: str
    direction: Direction
    amount: Money
    functional_minor: int | None = None

    def resolved_functional_minor(self) -> int:
        if self.functional_minor is None:
            if self.amount.currency != "PKR":
                raise ValueError("Non-PKR postings require an explicit PKR functional amount")
            return self.amount.minor
        if type(self.functional_minor) is not int or self.functional_minor < 0:
            raise ValueError("Functional amount must be non-negative integer PKR minor units")
        return self.functional_minor


@dataclass(frozen=True, slots=True)
class JournalResult:
    entry_id: str
    ledger_revision: int
    effective_date: date
