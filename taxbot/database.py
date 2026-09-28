"""SQLite connection, migration, and invariant validation."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable
from pathlib import Path

from .errors import MigrationError, ValidationError
from .migrations import LATEST_SCHEMA_VERSION, MIGRATIONS
from .util import utc_now


class ManagedConnection(sqlite3.Connection):
    """sqlite3 context manager that also releases the Windows file handle."""

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        try:
            return super().__exit__(exc_type, exc, traceback)
        finally:
            self.close()


class Database:
    def __init__(self, path: Path) -> None:
        self.path = Path(path).resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self, *, readonly: bool = False) -> ManagedConnection:
        if readonly:
            connection = sqlite3.connect(
                f"file:{self.path.as_posix()}?mode=ro",
                uri=True,
                isolation_level=None,
                factory=ManagedConnection,
            )
        else:
            connection = sqlite3.connect(
                self.path, isolation_level=None, factory=ManagedConnection
            )
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        if not readonly:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
        return connection

    def migrate(self, *, pre_migration_backup: Callable[[], None] | None = None) -> None:
        with self.connect() as connection:
            current = self._schema_version(connection)
            if current > LATEST_SCHEMA_VERSION:
                raise MigrationError(
                    f"Database schema {current} is newer than supported {LATEST_SCHEMA_VERSION}"
                )
            pending = [migration for migration in MIGRATIONS if migration[0] > current]
            if current > 0 and pending:
                if pre_migration_backup is None:
                    raise MigrationError("A pre-migration backup is required")
                pre_migration_backup()
            for version, name, sql in pending:
                if version <= current:
                    continue
                escaped_name = name.replace("'", "''")
                escaped_time = utc_now().replace("'", "''")
                script = (
                    "BEGIN IMMEDIATE;\n"
                    + sql
                    + f"\nINSERT INTO schema_migrations(version, name, applied_at) "
                    f"VALUES ({version}, '{escaped_name}', '{escaped_time}');\nCOMMIT;"
                )
                try:
                    connection.executescript(script)
                except sqlite3.Error as exc:
                    try:
                        connection.execute("ROLLBACK")
                    except sqlite3.Error:
                        pass
                    raise MigrationError(f"Migration {version} failed") from exc
                current = version

    @staticmethod
    def _schema_version(connection: sqlite3.Connection) -> int:
        exists = connection.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
        ).fetchone()
        if not exists:
            return 0
        row = connection.execute("SELECT COALESCE(MAX(version), 0) FROM schema_migrations").fetchone()
        return int(row[0])

    def schema_version(self) -> int:
        with self.connect(readonly=True) as connection:
            return self._schema_version(connection)

    def ledger_revision(self) -> int:
        with self.connect(readonly=True) as connection:
            row = connection.execute(
                "SELECT ledger_revision FROM system_state WHERE singleton = 1"
            ).fetchone()
            return int(row[0])

    def validate_invariants(self) -> dict[str, int | str]:
        with self.connect(readonly=True) as connection:
            integrity = str(connection.execute("PRAGMA integrity_check").fetchone()[0])
            foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
            unbalanced = connection.execute(
                """
                SELECT j.id
                FROM journal_entries j
                LEFT JOIN postings p ON p.journal_entry_id = j.id
                GROUP BY j.id
                HAVING COUNT(p.id) < 2 OR
                    SUM(CASE WHEN p.direction = 'debit' THEN p.functional_minor ELSE 0 END) !=
                    SUM(CASE WHEN p.direction = 'credit' THEN p.functional_minor ELSE 0 END)
                """
            ).fetchall()
            revision = int(
                connection.execute(
                    "SELECT ledger_revision FROM system_state WHERE singleton = 1"
                ).fetchone()[0]
            )
            max_revision = int(
                connection.execute(
                    "SELECT COALESCE(MAX(ledger_revision), 0) FROM journal_entries"
                ).fetchone()[0]
            )
        if integrity != "ok" or foreign_keys or unbalanced or max_revision > revision:
            raise ValidationError("Database invariant validation failed")
        return {
            "integrity": integrity,
            "foreign_key_errors": len(foreign_keys),
            "unbalanced_journals": len(unbalanced),
            "ledger_revision": revision,
            "schema_version": self.schema_version(),
        }
