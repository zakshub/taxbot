# Statement and document ingestion

## Workflow and adapter contract

User selects a file in the private store (or authorizes a selected Drive file); ingest hashes and preserves bytes, detects type, creates a batch, extracts immutable observations, normalizes fields, validates controls, proposes matches, and exposes exceptions before canonical acceptance.

## Phase 2 implementation checkpoint (2026-09-29)

The selected first target is a Meezan PKR current salaried account with searchable PDF statements. The schema and internal service now implement immutable extraction runs and observations, durable batch checkpoints, exact PKR controls, quarantine, coverage, duplicate candidates, idempotent commands, and all-or-nothing publication. Publication accepts observations into the canonical evidence layer; it does not create journal entries or classify credits/debits.

The Meezan PDF layout is still **UNKNOWN**. Meezan's public site confirms e-statements and statement download channels but does not document transaction headers, reading order, reference semantics, or control placement. No bank-specific layout was guessed. The current tests construct adapter outputs directly using wholly synthetic data. Completion requires a privacy-safe structural inspection followed by an invented layout fixture and parser drift tests. No real statement may enter the repository.

PDF text extraction remains an adapter boundary. The runtime currently has no bundled extractor, and no dependency has been added without validating the selected PDF. A later choice must preserve page/text-span locators, operate locally, reject scans or corrupt/password-protected inputs safely, and record its name/version/configuration digest.

Adapters accept a document reference, account hint, format/version, locale configuration, and idempotency key. They return observations, source locators, statement metadata, extracted control totals, per-field confidence and diagnostics. They never directly create approved ledger postings. The normalizer retains both raw and normalized values.

CSV/Excel adapters must handle encoding, delimiters, debit/credit columns, signed amounts, decimal/group separators, date locale, headers/footers and merged cells without guessing ambiguous values. Do not execute spreadsheet macros, external links, or formulas. Formula cells require safe cached-value handling or review, never evaluation of untrusted code.

PDF processing prefers text extraction; scans require local OCR. Preserve page and bounding-box/text-span location. Password-protected files pause for a locally supplied password held only for processing, never logged or committed. Low-quality extraction, missing pages, mixed accounts, or uncertain numeric fields quarantine affected observations.

## Batch lifecycle and recovery

`received -> quarantined -> extracting -> normalized -> validated -> ready -> accepted`; failures are recorded with retryable/nonretryable reason. Quarantine may require review before extraction or acceptance. Each step records a durable checkpoint and its input/output versions. A batch with unresolved structural errors cannot publish. Row-level unresolved classification may enter explicit clearing only under the [data model](DATA_MODEL.md) policy.

Canonical publication of the selected validated batch set is one database transaction, including links, audit records, idempotency result and ledger revision. A crash before commit leaves no canonical partial publication; a retry after commit returns the recorded result. Extraction retries produce separately identifiable runs; old outputs remain available.

The same bytes must reuse the stored document. Parser upgrades can reprocess them, but cannot silently replace accepted facts. Reprocessing produces a comparison and proposed corrections.

## Identity and deduplication

Three different identities are required: file hash, observation locator within an extraction run, and stable financial event ID. None substitutes for all others.

1. Exact duplicate file/command: reuse results or register a retry, never new postings.
2. Reliable bank transaction reference: match only within institution/account context and validated reference semantics; some banks reuse references.
3. Overlap candidates: compare account, currency, signed amount, date/value date, balance context, narration and statement sequence. Fingerprints generate candidates, not unconditional deletion.
4. Ambiguous duplicate: retain both observations and open review; distinguish two legitimate equal transactions from the same row reproduced in overlapping statements.
5. Reversal: preserve both original and reversal as separate economic events, linked explicitly. A reversal is not a duplicate.

## Validation and format drift

Validate account identity, ownership applicability, currency, statement coverage, row counts where supplied, and opening + credits - debits = closing under the adapter's declared convention. Where running balances exist, validate transitions. Missing control totals reduce assurance; absence of a mismatch does not establish completeness.

Record date gaps/overlaps by account and period. Test cross-year statements without assigning the entire file to one tax year. Unknown columns, changed layout signatures, debit/credit ambiguity, unexplained balance mismatches, and unexpected totals fail closed in staging. Parser versions and synthetic format fixtures must change together.

## Evidence documents (expanded in Phase 4)

Support salary/withholding certificates, investment statements, property and vehicle records, receipts, loan statements, prior returns and acknowledgements. Extraction creates proposed facts with per-field confidence, document kind, taxpayer/account association, period, currency, source locator and extractor version.

Matching uses amount, date/period, counterparties, account references and document identifiers, with many-to-many allocations described in [Matching](MATCHING_ENGINE.md). A salary certificate can explain gross salary, deductions and net deposits; it is not another salary receipt. A withholding certificate and bank tax debit can describe the same deduction.

Conflicting sources create a discrepancy review; do not simply prefer the newest file. Document replacement preserves both hashes and the supersession decision. A missing certificate is a coverage gap, never a zero withholding amount.

## Optional integration and failure behavior

Drive is a source adapter only, with explicit selected-file authorization and local copy validation. Sheets/Excel review round trips follow [Architecture](ARCHITECTURE.md). Missing network access, expired OAuth, OCR/model unavailability or unsupported formats must leave local originals intact and permit later retry or explicit manual fact entry with evidence.

Manual fallback is structured and audited: select source/locator, enter the missing fact, state reason, confirm. It is not an untracked spreadsheet workaround.
