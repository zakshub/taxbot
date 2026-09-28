"""Domain errors with stable, non-sensitive operational codes."""


class TaxbotError(Exception):
    """Base class for expected application errors."""

    code = "taxbot_error"


class ValidationError(TaxbotError):
    code = "validation_error"


class MoneyError(ValidationError):
    code = "money_error"


class UnbalancedJournalError(ValidationError):
    code = "unbalanced_journal"


class StaleRevisionError(TaxbotError):
    code = "stale_revision"


class IdempotencyConflictError(TaxbotError):
    code = "idempotency_conflict"


class NotFoundError(TaxbotError):
    code = "not_found"


class StorageSecurityError(TaxbotError):
    code = "storage_security_error"


class MigrationError(TaxbotError):
    code = "migration_error"


class BackupError(TaxbotError):
    code = "backup_error"
