"""Minimal local operations for Phase 1 setup, status, backup, and restore drills."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .backup import BackupManager
from .ledger import LedgerService
from .storage import StorageMode, StoragePolicy


def _policy(args: argparse.Namespace) -> StoragePolicy:
    repository = Path(__file__).resolve().parent.parent
    return StoragePolicy(
        root=Path(args.root),
        repository_root=repository,
        mode=StorageMode(args.mode),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Taxbot Phase 1 local-ledger operations")
    parser.add_argument("--root", required=True, help="Private or synthetic storage root")
    parser.add_argument(
        "--mode", choices=[item.value for item in StorageMode], default="synthetic"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init", help="Initialize an empty store")
    subparsers.add_parser("status", help="Show redacted operational counts and invariants")
    subparsers.add_parser("backup", help="Create a consistent protected-root backup")
    restore = subparsers.add_parser("restore-drill", help="Verify and restore a backup")
    restore.add_argument("backup_dir")
    restore.add_argument("target")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    policy = _policy(args)
    if args.command == "init":
        output = LedgerService.setup_empty_store(policy)
    elif args.command == "status":
        output = LedgerService(policy).operational_status()
    elif args.command == "backup":
        output = {"backup_dir": str(BackupManager(policy).create())}
    elif args.command == "restore-drill":
        output = BackupManager(policy).restore_drill(
            Path(args.backup_dir), Path(args.target)
        )
    else:  # pragma: no cover - argparse constrains this
        raise AssertionError("Unknown command")
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0
