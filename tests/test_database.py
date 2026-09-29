from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from taxbot.database import Database
from taxbot.errors import MigrationError
from taxbot.ledger import LedgerService
from taxbot.migrations import MIGRATIONS
from taxbot.storage import StoragePolicy


class MigrationTests(unittest.TestCase):
    def test_future_migration_requires_pre_migration_backup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            database = Database(Path(directory) / "ledger.sqlite3")
            database.migrate()
            next_version = MIGRATIONS[-1][0] + 1
            extended = MIGRATIONS + (
                (next_version, "synthetic_probe", "CREATE TABLE migration_probe(id INTEGER);"),
            )
            with patch("taxbot.database.MIGRATIONS", extended), patch(
                "taxbot.database.LATEST_SCHEMA_VERSION", next_version
            ):
                with self.assertRaises(MigrationError):
                    database.migrate()
                calls: list[str] = []
                database.migrate(pre_migration_backup=lambda: calls.append("backed-up"))
            self.assertEqual(calls, ["backed-up"])
            self.assertEqual(database.schema_version(), next_version)

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

    def test_ledger_service_backs_up_existing_store_before_upgrade(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "synthetic"
            policy = StoragePolicy(root, Path.cwd())
            policy.prepare_directories()
            database = Database(policy.database_path)
            with patch("taxbot.database.MIGRATIONS", MIGRATIONS[:1]), patch(
                "taxbot.database.LATEST_SCHEMA_VERSION", 1
            ):
                database.migrate()
            LedgerService(policy)
            self.assertEqual(database.schema_version(), MIGRATIONS[-1][0])
            backups = [path for path in policy.backups_root.iterdir() if path.is_dir()]
            self.assertEqual(len(backups), 1)
            self.assertTrue((backups[0] / "manifest.json").is_file())


if __name__ == "__main__":
    unittest.main()
