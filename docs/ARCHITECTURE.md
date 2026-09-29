# Architecture and system boundaries

## Structure

Implemented baseline: Python modular monolith, SQLite local database, private content-addressed document storage, one process/single writer, and the Phase 2 bank-neutral statement staging/publication core. There is no frontend, HTTP API, scheduler service, message broker, ORM, bank-specific parser, tax engine or filing adapter. Modules invoke typed internal commands and queries; the command line is limited to storage setup, redacted status, backup and restore drills.

```text
Local files / optional selected Drive files
  -> immutable document store -> quarantine / extraction / observations
  -> normalization / dedup / transfer candidates / classification proposals
  -> review and controlled acceptance -> balanced canonical journal
  -> asset / liability / withholding subledgers and coverage checks
  -> continuous reconciliation -> year-specific Pakistan tax engine
  -> Shadow IRIS -> versioned field mapping -> immutable Filing Manifest
  -> human manifest approval -> assisted entry / read-back
  -> discrepancy gate -> separate human submission approval -> receipt
```

Evidence is stored from Phase 1, before advanced extraction in Phase 4. Posting, evidence linking, revision increments, and audit events commit atomically. Read models and snapshots are rebuildable; originals and accepted history are not disposable caches.

## Sources of authority

Original documents establish what was supplied; observations establish what was extracted; the accepted ledger establishes financial facts; reviewed rule packages determine tax treatment; an approved manifest establishes permitted filing values. Conflicts between these layers create review items, not silent precedence or overwrite.

SQLite is the operational source of truth, with external document objects referenced by hash. Spreadsheet copies, AI responses, browser drafts, and third-party prefilled values are not authoritative. The latest accepted ledger revision and immutable filed snapshot can coexist without changing what was actually submitted.

## Internal contracts (design only)

| Boundary | Input | Output and constraints |
|---|---|---|
| Ingest | File reference, account hint, adapter/version, idempotency key | Batch and immutable observations, control totals, diagnostics; no accepted postings |
| Propose | Observations and active ownership/category rules | Duplicate, transfer, category and evidence candidates with reasons/confidence |
| Accept | Candidate revision, actor/policy, evidence, expected ledger revision | Atomic journal event and audit event; stale decisions rejected |
| Correct | Target record revision, reason, replacement evidence | Superseding record or reversal/replacement journal; dependent outputs stale |
| Reconcile | Taxpayer, period/as-of date, ledger revision, rule status | Independent balances, coverage gaps, residual and unresolved causes |
| Compute tax | Closed snapshot and approved tax rule package | Semantic return values and calculation lineage, or explicit unsupported results |
| Build manifest | Semantic return, mapping and validation versions | Immutable exact values, lineage and content hash; no approval inferred |
| File | Manifest plus matching approval | Read-back/discrepancy record and, after separate approval, receipt |

All mutating commands carry stable idempotency keys and expected revisions. Validation failure produces no partial canonical change. Errors distinguish bad input, ambiguous facts, unsupported treatment, transient transport failure, and drift. Only safe idempotent transport work may retry automatically with bounded backoff; ambiguities require review.

## Optional Google Drive and spreadsheet adapters

- Google Drive input: import explicitly selected files into the local immutable store; record remote file ID/version and local byte hash. Changed remote content creates a new document revision. A failed/revoked connection does not block local use.
- Google Drive backup: upload completed encrypted snapshot archives with manifests/checksums. Never place a live SQLite file, WAL, or unencrypted originals in a synchronized folder. Local/offline backup remains available.
- Sheets/Excel: export read models with opaque record IDs, ledger revision, export ID, and allowed decision columns. Re-imported edits are proposed commands checked against the base revision and allowed fields. Formulas, altered IDs, stale values, and conflicts do not directly update the ledger. Escape formula-triggering untrusted text in exports.
- Sharing private report values is separate consent from cloud AI. Do not assume redaction makes detailed financial data anonymous.
- Use narrow per-file OAuth access where feasible. It does not imply access to every existing file in a folder. OAuth setup and provider retention behavior require validation before enabling integration.

Google's [scope guide](https://developers.google.com/workspace/drive/api/guides/api-specific-auth) confirms per-file `drive.file` access. Its [application-data guide](https://developers.google.com/workspace/drive/api/guides/appdata) says app data can be deleted by users or app removal; it is not the sole recovery store. Sources reviewed 2026-09-28. No connector is configured through Phase 1.

## Operations and failure isolation

Persist batch/run checkpoints in SQLite; use a local restartable work loop rather than distributed queues. Crash recovery checks incomplete runs before retrying. Staged blobs are written completely and hashed before references publish; interrupted/unreferenced blobs are quarantined and can be cleaned only after retention checks.

Expose private operational summaries: last successful import/backup, account coverage, failed batches, review age, unmatched transfers, reconciliation residual, stale rules/mappings, and filing state. Ordinary logs contain run IDs, event codes, counts, durations, and redacted errors. Financial values, narratives, OCR text, and identifiers belong only in access-controlled financial records, never telemetry.

Schema and parser migrations are explicit versions. Unknown/new bank layouts fail closed in staging. IRIS drift blocks the adapter while manual use of the manifest remains possible. Regulatory changes stale affected calculations. No automatic dependency or rule update may silently change an approved filing.
