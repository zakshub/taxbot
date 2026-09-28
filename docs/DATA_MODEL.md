# Canonical data model

This is a logical schema specification, not a migration or implementation. Its invariants apply to later SQLite schemas and internal command contracts in [Architecture](ARCHITECTURE.md).

## Shared conventions

Use application-generated UUIDs as stable opaque primary keys. Foreign keys are enforced. Every mutable aggregate has a revision; accepted corrections append a new revision with actor, reason, UTC timestamp, and predecessor reference. Original bytes, observations, posted journals, audit events, approved manifests and filed snapshots are immutable. Rejected/proposed records remain historical evidence of decisions.

Money uses exact decimal arithmetic. Persist posting amounts as integer minor units with a currency/scale registry; use canonical decimal strings for rates, quantities, tax calculations and intermediate values. No SQLite REAL or binary float for money. Rounding happens only at documented boundaries. Keep original-currency amount and PKR book amount, FX source/date/rate, and a separately derived tax conversion where rules differ. Unknown FX conversion blocks posting when required, not ingestion.

Use local ISO dates for transaction date, value date, document issue date, and legal effective dates. Store processing timestamps in UTC and render in Asia/Karachi. Tax-year assignment is a rule-derived fact; it is not inferred from import time. TY2027 boundaries are inclusive 2026-07-01 through 2027-06-30.

## Entities and constraints

Required fields below are minimum contracts; optional source fields must distinguish missing from zero/empty.

| Entity | Required information and relationships | Identity / integrity |
|---|---|---|
| TaxpayerProfile | ID, profile revision, residency applicability status, private identifier reference | One active taxpayer in v1; never put identifiers in fixtures or repository configuration |
| TaxYear | Taxpayer, year label, start/end, lifecycle state, baseline snapshot | Unique taxpayer/year; period does not overlap another ordinary year for that taxpayer |
| FinancialAccount | Institution, account kind, currency, private identifier reference, status | External bank/wallet/cash/investment account; account aliases are not primary keys |
| AccountOwnership | Account, owner reference, share, effective start/end, evidence, review status | Shares and dates validated; uncertain/joint ownership blocks whole-account transfer assumptions |
| LedgerAccount | Taxpayer, stable code, class (asset/liability/equity/income/expense/clearing), currency policy | Unique taxpayer/code; financial accounts map explicitly to ledger accounts |
| Counterparty / Alias | Counterparty ID, alias text/source, relationship proposal or confirmation | Alias matching never proves ownership; merges preserve predecessor IDs |
| Document | Content hash, object reference, MIME type, byte length, receipt time, document kind | Hash identifies identical bytes, not necessarily identical economic evidence |
| ImportBatch | Document references, account hint, adapter/version, run key, state, period/control totals | Unique accepted command key; retain all attempts and diagnostics |
| ExtractionRun | Document, extractor/version, configuration digest, timestamp, result references | New version creates new results; original extraction is retained |
| SourceObservation | Batch/run, document, locator, raw fields, normalized fields, extraction confidence | Unique run/document/locator/ordinal; row identity is distinct from financial identity |
| FinancialEvent / JournalEntry | Taxpayer, dates, event type, revision, acceptance actor/policy, source links | Stable event ID across corrections; journal revisions cannot mutate posted amounts |
| Posting | Journal, ledger account, debit or credit, currency amount, PKR book amount | Exactly one debit/credit direction; journal debits equal credits in functional PKR |
| ObservationEventLink | Observation, financial event, role, amount/allocation where applicable | Many observations can corroborate one event; no second posting by virtue of another source |
| MatchDecision | Candidate IDs, match kind, algorithm/version, features, score, decision, actor | Scoped to input revisions; uniqueness prevents consuming the same economic leg twice |
| TransferGroup | Member events/observations, ownership evidence, principal allocations, fee/FX links | Principal conservation checked; one event may split only through explicit allocations |
| Classification | Target/revision, category, method, model/rule version, confidence, reason/evidence | Proposal history retained; tax treatment is a separate result |
| ReviewItem / Decision | Target revision, reason, severity, alternatives, state, actor/evidence | Decisions against stale targets rejected; resolved history retained |
| RecurringPattern | Counterparty/account context, cadence/amount pattern, evidence window | Suggestion only; never generates an actual event |
| EvidenceAllocation | Document/extracted fact, event/claim, role, amount, currency, capacity group | Monetary allocations cannot exceed supported capacity; corroboration links do not consume money twice |
| Asset / AssetEvent | Asset ID, kind, ownership, dates, event type, journal/evidence links, value bases | Lifecycle projection references journal; never separately adds the same bank wealth twice |
| Liability / LiabilityEvent | Liability ID, lender, principal currency, terms evidence, lifecycle event, journal link | Principal and interest separated; refinance links old/new liabilities |
| WithholdingRecord | Deductor reference, date/period, section if known, gross base if known, deducted amount, evidence | Deduction is an observed fact; claimability belongs to versioned tax results |
| RulePackage / TaxResult | Tax year, version, effective periods, source references, applicability, status; inputs/results | Immutable approved package; results bind exact input revision and rules |
| ReconciliationSnapshot | Taxpayer/period, ledger revision, rule version/status, balances, bridge, coverage, blockers | Rebuildable but retained when used in approval/filing |
| FieldMapping | Tax year/form version, semantic path, target identity, entry/computed mode, transform | Explicit applicability and precision; no guessed field codes |
| FilingManifest | Schema version, year/profile reference, snapshot, rules/mapping versions, fields, lineage, hash | Immutable canonical payload; approval excluded from hash payload and references hash |
| Approval | Actor, timestamp, purpose, manifest hash, validation result reference | Manifest approval and final submission approval are different records |
| FilingRun / Receipt | Manifest hash, adapter/form version, state/checkpoints, read-back, approval references, receipt | Preserve unknown outcome; no automatic resubmission |
| AuditEvent | Actor, action, target/revisions, reason, run ID, timestamp | Append-only through application; not claimed tamper-proof against machine administrator |

## Journal and correction semantics

Each accepted financial event contains balanced postings and source links. Different-currency legs use explicit FX/conversion and clearing accounts; do not assert that USD debits equal PKR credits. Bank and tax balances may use different valuations, reconciled explicitly.

Unknown category can post to an explicit unresolved clearing account when the amount/account is reliable; it remains a blocking issue for closing if it affects filing. It must not disappear into miscellaneous expenses. Clearing balances are visible and cannot be silently written off.

Correct posted amounts by reversal plus replacement, both linked to the original event. Correct nonfinancial metadata through superseding revisions. Duplicate decisions may retract an erroneous accepted event with a reversal, retaining its observations. Invalidating any dependency marks affected snapshots/manifests stale; filed snapshots remain immutable.

## Provenance and assurance

`method`: machine_proposed, rule_derived, user_supplied. `review_status`: proposed, accepted, user_confirmed, verified, rejected, superseded. Method does not change when a human confirms a machine proposal. Accepted means allowed into the working ledger, not certified for filing.

Verification requires a verification record describing checks, actor (human or named deterministic verifier), evidence, versions, and time. AI cannot grant verification. Material filing facts require source-backed verification or an explicit supported human attestation; an attestation cannot override an unsupported legal treatment or unavailable mapping.

Lineage forms a directed dependency graph: original/locator -> extracted observation -> accepted event/fact -> aggregation/calculation -> semantic return -> mapped manifest value. Every calculation stores input IDs and versions, not only a text explanation.

## Retention responsibility

The private store retains originals, accepted history and filed artifacts together. User-controlled deletion requires a retention review; legal retention periods remain a research gate in [Security](SECURITY.md). Derived caches can be regenerated, but evidence used for a filed value cannot be removed casually. Database migrations and backups must preserve referential integrity and document hashes.
