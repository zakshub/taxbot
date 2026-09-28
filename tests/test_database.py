from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from taxbot.database import Database
from taxbot.errors import MigrationError
from taxbot.migrations import MIGRATIONS


class MigrationTests(unittest.TestCase):
    def test_future_migration_requires_pre_migration_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "ledger.sqlite3")
            database.migrate()
            extended = MIGRATIONS + ((2, "synthetic_probe", "CREATE TABLE migration_probe(id INTEGER);"),)
            with patch("taxbot.database.MIGRATIONS", extended), patch(
                "taxbot.database.LATEST_SCHEMA_VERSION", 2
            ):
                with self.assertRaises(MigrationError):
                    database.migrate()
                calls: list[str] = []
                database.migrate(pre_migration_backup=lambda: calls.append("backed-up"))
            self.assertEqual(calls, ["backed-up"])
            self.assertEqual(database.schema_version(), 2)

    def test_newer_unknown_schema_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "ledger.sqlite3")
            database.migrate()
            with database.connect() as connection:
                connection.execute(
                    "INSERT INTO schema_migrations(version, name, applied_at) VALUES (999, 'future', 'synthetic')"
                )
            with self.assertRaises(MigrationError):
                database.migrate()


if __name__ == "__main__":
    unittest.main()
