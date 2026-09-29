"""Taxbot local ledger and statement-ingestion foundation."""

from .ingestion import StatementExtraction, StatementIngestionService, StatementObservation
from .ledger import LedgerService
from .money import Money
from .storage import StorageMode, StoragePolicy

__all__ = [
    "LedgerService",
    "Money",
    "StatementExtraction",
    "StatementIngestionService",
    "StatementObservation",
    "StorageMode",
    "StoragePolicy",
]
__version__ = "0.2.0a1"
