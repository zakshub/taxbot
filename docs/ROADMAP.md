# Roadmap and planning status

This roadmap is dependency-ordered. A phase may perform its stated research and synthetic implementation only after the preceding gate passes. It does not authorize implementation: Phase 0 planning must be reviewed first. Security, provenance, migration and observability work begin where needed and continue across phases rather than becoming a late hardening exercise.

## Phase gates

### Phase 0 — Planning and research

Deliver the requirements, architecture, data model, workflows, decision record, research register, security/testing approach and phase acceptance gates. Classify external claims and eliminate contradictions. Publish documentation only.

Acceptance: R01–R23 map to owners/gates; sources and unknowns are dated; links and scenario walkthroughs pass; staged content contains no private data, dependencies or feature implementation; documentation-only commit is pushed.

### Phase 1 — Canonical financial ledger

Status: **complete; acceptance review passed (2026-09-28).** No real taxpayer data was used.

Implement the local database/domain core using synthetic data: taxpayer/year references, financial and ledger accounts, ownership periods, document metadata/hashes, balanced journal, exact money, provenance, audit/corrections, schema migrations, storage preflight, backup and restore. Provide only minimal local commands needed to exercise the core—no product UI, bank parser or tax rules.

Acceptance: exact arithmetic and foreign-key/invariant tests pass; synthetic opening positions and balanced events work; same-owner transfer can be represented without income/expense; command retries are idempotent; stale revisions are rejected; corrections reverse/supersede rather than mutate; evidence links and audit history survive migration and verified backup restore; real-data mode fails closed until an approved encrypted root is configured; logs reveal no financial payloads.

### Phase 2 — Bank statement ingestion

Status: **in progress (authorized 2026-09-29).** Target: Meezan PKR current salaried account, searchable PDF. Implemented checkpoint: versioned schema, immutable observations/extraction lineage, batch checkpoints, exact controls, quarantine, overlap candidates, coverage and atomic observation publication using synthetic adapter outputs. Remaining gate: verified Meezan structure, local PDF text extractor, bank-specific parser/fixtures and drift/error tests. Phase 3 remains unauthorized.

Select one actual bank/product format based on private portfolio input, then build its adapter against constructed synthetic fixtures. Add staging, normalization, control totals, period coverage, duplicate candidates and resumable atomic publication for CSV/Excel or PDF according to the chosen format.

Acceptance: repeat and overlapping imports create no duplicate postings; legitimate equal transactions survive; reversals and year boundaries are retained; malformed/changed formats quarantine; opening/closing/running controls identify omissions; source locators and parser versions survive reprocessing; interrupted batches recover without partial canonical publication.

Checkpoint verification: 30 standard-library tests pass with `ResourceWarning` promoted to an error. Synthetic adapter-output tests cover idempotent staging/publication, conflicting run identity, overlap candidates without deletion, balance mismatch quarantine, unreadable-field retention, explicit format-drift quarantine, year-boundary/reversal retention, immutable locators/extractor versions, and zero journal creation. Schema upgrades create a consistent pre-migration backup. This does **not** satisfy the complete Phase 2 gate because a local PDF extractor and verified Meezan layout adapter do not yet exist.

### Phase 3 — Classification and matching

Add counterparties/aliases, transfer groups, deterministic categories, recurring suggestions, confidence/reasons and the review workflow. Evaluate AI only after a labeled set exists; keep cloud AI disabled unless separately approved.

Acceptance: synthetic same-owner, fee, split, delayed, FX and missing-leg cases behave as specified; unrelated equal amounts are not forced into transfers; loan/asset principal is not income/expense; low-confidence, conflicting and material cases queue; stale decisions fail; confidence is never rendered as verification; measured false positives and limitations are recorded.

### Phase 4 — Documents and evidence

Add secure local extraction/OCR interfaces for selected salary, withholding and financial evidence types, document revisions, component facts and many-to-many allocations. Optionally add explicitly selected Drive input only after OAuth/privacy review.

Acceptance: originals/hashes and page/cell locators persist; extractor upgrades produce comparisons; conflicts queue; allocation capacity prevents double counting; a certificate and bank transaction can corroborate one event; malicious/unsupported files quarantine safely; cloud remains opt-in; Drive failure has a local fallback.

### Phase 5 — Assets and liabilities

Implement opening schedules and lifecycle projections for applicable asset/liability kinds, maintaining value bases and principal/interest distinctions. Import TY2026 filed values separately from corrected economic evidence.

Acceptance: synthetic acquisition/addition/disposal/transfer and drawdown/repayment/refinance/forgiveness roll forward; journals and subledgers agree; purchase/disposal and loan principal are not double-counted; unsupported ownership/basis remains visible; prior-filed discrepancies cannot be silently overwritten.

### Phase 6 — Continuous reconciliation

Build account coverage, balance checks, subledger checks, gross/net and withholding consistency, economic wealth bridge, rule-versioned filing bridge, snapshots and year lifecycle.

Acceptance: the coherent synthetic year reconciles; introduced gaps, duplicate components and errors produce explained blockers; a zero residual with missing coverage fails closing; no plug entry clears residuals; post-approval changes stale results; post-filing correction creates a revision case while preserving the filed snapshot.

### Phase 7 — Pakistan tax engine

Research actual applicability and encode only reviewed TY2027 rules from authoritative sources, with effective dates, legal citations, versions, exact calculations and boundary cases. Obtain qualified review for material ambiguity.

Acceptance: source/reviewer records exist for every approved rule; applicable scenarios and thresholds/rounding pass independent worked examples; enacted and proposal sources are distinguished; unsupported categories block complete approval; historical package calculations reproduce; amendments create explicit diffs and renewed review.

### Phase 8 — Shadow IRIS and Filing Manifest

Model the complete applicable semantic return, verify the current TY2027 form mapping, add coverage/validation, deterministic manifests, exports and approval invalidation. Sheets/Excel may be added as revision-bound review projections.

Acceptance: each material value traces to evidence and rules; missing/zero/not-applicable differ; mapping source/version is verified; hash is deterministic; complete applicable coverage and reconciliation are mandatory; changed dependencies invalidate approval; stale spreadsheet edits cannot write the ledger; manifest approval is immutable and distinct from submission approval.

### Phase 9 — Assisted IRIS automation

After access/terms/form research, implement a mock adapter and then a narrowly authorized live assisted adapter if viable. It consumes approved manifests, handles authentication pauses, writes drafts, reads back values and stops at discrepancy/submission approval gates.

Acceptance: mocks prove version preflight, existing-draft conflicts, safe resume, read-before-retry, CAPTCHA/OTP human pauses, unknown fields/calculations, complete read-back and unknown submission outcomes; live access is enabled only with confirmed scope; the adapter cannot invent values; final submission cannot occur without fresh distinct approval; manual manifest entry remains tested.

### Phase 10 — Hardening and TY2027 filing readiness

Revalidate applicable law, form/mapping, deadlines and integrations; run the private end-to-end workflow, security/restore drills, independent review and manual fallback. Resolve or accept documented blockers before filing.

Acceptance: current rule/form packages are approved; expected account/evidence coverage is complete; all blocking reviews resolved; private rehearsal reproduces the manifest and read-back; backup restore and migration recovery pass; browser/format drift monitoring and rollback procedures work; submission checklist and manual fallback pass; actual submission still awaits explicit approval.

## Implementation Status

### Phase 1 delivered

- Standard-library Python package and versioned SQLite migration; no runtime framework or third-party dependency.
- Exact minor-unit money, PKR functional postings, taxpayer/year, financial/ledger accounts and dated ownership records.
- Atomic balanced journals, optimistic ledger revision, command idempotency, immutable source/document/journal/audit records, evidence links and reversal-plus-replacement corrections.
- Content-addressed document objects, redacted operational status and explicit synthetic/real storage modes.
- BitLocker-gated real-data root outside Git/sync paths; restore receipt required before normal real-data access.
- Consistent SQLite backups with referenced-object hashing, corruption detection and isolated restore drills.
- Future migrations require a pre-migration backup callback; unknown future schema versions fail closed.

### Phase 1 verification

On Python 3.13.15, 22 standard-library tests pass with `ResourceWarning` promoted to errors. Bytecode compilation and CLI smoke checks pass. Tests cover exact money, journal balance/atomicity, stale revisions, idempotency, immutability, evidence, corrections, ownership limits, internal transfers, income/expense/loan/asset distinctions, FX functional amounts, migration guards, BitLocker/sync-root storage gates, and backup/restore preservation and corruption detection.

### Phase 1 acceptance review

**PASS (2026-09-28).** Every Phase 1 acceptance item is implemented and exercised: exact money and balance invariants; accounts/ownership, evidence hashes and stable IDs; idempotent atomic commands and stale-revision rejection; immutable audit/correction history; semantic transfer/loan/asset examples; versioned migration and backup requirements; isolated verified restore; fail-closed real-data storage; and redacted operational status. No forbidden Phase 2 or later feature was introduced.

No real-data root was provisioned and no real taxpayer data was processed. Phase 2 was subsequently authorized for Meezan PKR current salaried searchable-PDF statements. The bank-neutral ingestion core uses synthetic data only; the exact PDF structure remains an external input and no bank-specific support is claimed yet.

## Planning Status

### Planning review outcome

Technical review completed on 2026-09-28: **PASS**. It enabled the subsequently authorized Phase 1 implementation. The review traced every requested topic to an owning document, walked the mandatory synthetic scenarios, checked external-claim labels and approval boundaries, resolved local Markdown links, and scanned the publication set for implementation files, credentials and taxpayer identifiers.

No contradiction was found between the ledger, evidence, reconciliation, tax, manifest and filing layers. In particular, journal balance is not treated as statement completeness; a zero wealth residual is not treated as complete evidence; confidence is not treated as verification; withholding observed is not treated as automatically claimable; and manifest approval is not treated as submission approval.

The remaining open questions and external blockers are placed at later gates. Windows BitLocker has since been selected and implemented as the real-data storage gate; actual private-root provisioning and recovery-key custody remain user operational steps before any real data.

### Completed planning

- Product requirements R01–R23, system boundaries, canonical authority and internal contracts.
- Logical schema, identity/correction/provenance semantics and exact money rules.
- Import, normalization, deduplication, transfer/classification/review and evidence workflows.
- Asset/liability lifecycles, continuous controls, year closing and approval invalidation.
- Tax-rule packaging, Shadow IRIS, Filing Manifest and assisted-filing boundaries.
- Local-first security, private storage gate, backup/restore, migrations, observability and testing.
- Dated FBR, IRIS and Pakistan banking research registers with uncertainty labels.

### Decisions made

- One resident individual on one Windows PC; Python modular monolith and SQLite baseline, now implemented for Phase 1.
- Balanced journal plus immutable observations and append-only correction/audit history.
- Local-first processing; cloud AI disabled until opt-in/provider review; initial AI auto-acceptance disabled.
- File-first bank ingestion; no assumption of usable personal bank or annual-return API.
- Tax rules, Shadow IRIS mapping, browser selectors, manifest approval and submission approval are independent layers.
- Real data stays in a verified encrypted private root outside Git; spreadsheets are revision-bound projections.

### Open questions

- What exact headers, columns, page locators and control-total placement occur in the selected Meezan searchable PDF?
- Which income, asset, liability, foreign-currency and withholding categories apply privately?
- Does verified TY2026 closing evidence agree with economic opening positions?
- Where will the BitLocker-protected private root and separately protected backup/recovery key be provisioned?
- Is a cloud AI provider ever acceptable, and for which minimized data classes?

### Research still required

- Finance Act 2026 and applicable amendments/rules/notifications; TY2027 return schema, instructions and filing deadline.
- Detailed withholding treatment and reconciliation presentation for each applicable source.
- Current Liberated Model/API/ADX eligibility and support, IRIS automation conditions, authentication/draft/save/submission behavior.
- Bank-specific export availability, layouts/reference semantics and any genuinely usable read-only API.
- Statutory record retention, privacy obligations and treatment of unresolved taxpayer-specific cases.

### Technical risks

- Bank/PDF format drift, ambiguous duplicate/transfer matches and incomplete cash/non-bank evidence.
- Gross/net or evidence corroboration errors that double-count income/withholding.
- SQLite/document snapshot inconsistency, encryption gaps in temp/browser paths and unrecoverable keys.
- Uncalibrated AI confidence, prompt-injection content, spreadsheet formula injection and private diagnostics.
- Rule/form/UI changes invalidating calculations, mappings, approvals or automation during filing season.

### External blockers

- Authoritative complete TY2027 rule/form materials and later amendments may change.
- FBR integration eligibility, automation conditions, current UI and sandbox availability are UNKNOWN.
- Personal transaction-history APIs across the taxpayer's banks are UNKNOWN.
- Real-data work is blocked until private encrypted storage, keys and restore are verified.
- Complete filing is blocked by unresolved material legal questions or missing taxpayer evidence, regardless of software progress.

### Recommended first implementation milestone — completed

Phase 1 delivered the canonical ledger and secure local foundation using synthetic data only. It excludes UI, bank parsers, tax rules, AI and IRIS automation.

### Acceptance criteria for that milestone

- Exact-money balanced journal, accounts/ownership, stable IDs, revisions, source hashes and evidence links implemented.
- Idempotent commands, optimistic revision checks, atomic posting and append-only correction/audit behavior verified.
- Synthetic opening positions, ordinary income/expense, same-owner transfer and asset/liability exchange represented without semantic double counting.
- Versioned migration, pre-migration backup, isolated restore and invariant verification pass.
- Secure-root preflight rejects repository/sync placement and blocks real data until an approved encrypted boundary is configured.
- Redacted operations expose status/error codes without financial content; no frontend/framework/parsers/IRIS work introduced.

### Recommended implementation order — completed

1. Resolve the Phase 1 private-root encryption and recovery decision; write the schema/invariant design against this plan.
2. Implement exact money, IDs/revisions, taxpayer/year, accounts/ownership and balanced journal.
3. Add document metadata/hashes, lineage, audit events, idempotency and correction workflows.
4. Add migration, consistent backup/restore, storage preflight and redacted operational status.
5. Complete synthetic scenarios and Phase 1 acceptance review; stop before selecting/building a bank adapter.

The next action is explicit Phase 2 authorization plus the non-sensitive identity of the first bank/product and available statement format. Phase 2 must not begin from this status update alone.
