# Product requirements and vision

## Outcome

Prepare a traceable return throughout the year rather than reconstructing it at filing time. The taxpayer supplies files and resolves ambiguity; deterministic processing does the repeatable work. Every material filed value must be explainable from evidence, confirmed facts, and a versioned calculation.

Initial audience: one Pakistan resident individual operating one Windows PC. Potential coverage includes salary, bank profit, investments, property, vehicles, personal expenditure, loans, gifts, and remittances. These are capabilities to assess, not assertions about this taxpayer. Business income, foreign income, residency complexity, and unusual instruments require explicit coverage research before filing. Recording an event must remain possible even when its tax treatment is unsupported.

Not in initial scope: SaaS, multi-tenant access control, autonomous banking, payment initiation, universal bank connectors, independent legal advice, or autonomous submission. A taxpayer identifier provides a future extension point without designing tenancy now.

## Requirements and traceability

Phase numbers refer to [roadmap acceptance gates](ROADMAP.md). Each row has one primary owner; supporting documents link to that owner.

| ID | Required behavior | Specification owner | Gate |
|---|---|---|---|
| R01 | Local structured ledger is authoritative; minimize repeated entry; single taxpayer | [Architecture](ARCHITECTURE.md) | P1 |
| R02 | Accounts, ownership periods, counterparties, exact money and dates | [Data model](DATA_MODEL.md) | P1 |
| R03 | Immutable observations, stable identities, journal balance, lineage and corrections | [Data model](DATA_MODEL.md) | P1 |
| R04 | CSV/Excel/PDF staging, import batches, normalization, control totals and recovery | [Ingestion](INGESTION.md) | P2 |
| R05 | Safe deduplication, overlapping statements, reversals and bank-format changes | [Ingestion](INGESTION.md) | P2 |
| R06 | Same-owner transfers, split/FX/fee handling, counterparty resolution | [Matching](MATCHING_ENGINE.md) | P3 |
| R07 | Rule-first classification, AI confidence, review, recurring suggestions | [Matching](MATCHING_ENGINE.md) | P3 |
| R08 | Document extraction and many-to-many evidence matching without double counting | [Ingestion](INGESTION.md) | P4 |
| R09 | Asset opening, acquisition, additions, disposal, transfer and closing | [Asset/liability lifecycles](ASSETS_AND_LIABILITIES.md) | P5 |
| R10 | Liability drawdown, repayment, refinance, interest, forgiveness and closing | [Asset/liability lifecycles](ASSETS_AND_LIABILITIES.md) | P5 |
| R11 | Income/expenditure coverage, withholding checks and continuous wealth bridge | [Reconciliation](RECONCILIATION.md) | P6 |
| R12 | TY2026 baseline, year closing, approval invalidation and post-filing correction | [Reconciliation](RECONCILIATION.md) | P6 |
| R13 | Independent Pakistan rules, legal sources, tax-year versioning, credit eligibility | [Tax engine](TAX_ENGINE.md) | P7 |
| R14 | Shadow IRIS, versioned field mapping, exact manifest, complete provenance | [Tax engine](TAX_ENGINE.md) | P8 |
| R15 | Manifest approval, approved-only entry, read-back and discrepancy checks | [IRIS automation](IRIS_AUTOMATION.md) | P8/P9 |
| R16 | Authentication pauses, CAPTCHA/OTP boundaries, separate submission approval | [IRIS automation](IRIS_AUTOMATION.md) | P9 |
| R17 | Private encrypted storage, secrets, Git exclusions, opt-in cloud AI | [Security](SECURITY.md) | P1/P4 |
| R18 | Consistent encrypted backups, recovery keys, restore and schema migrations | [Security](SECURITY.md) | P1/P10 |
| R19 | Optional Drive ingestion/backup and Sheets/Excel review projections | [Architecture](ARCHITECTURE.md) | P4/P8 |
| R20 | Durable recovery, redacted observability and error ownership | [Architecture](ARCHITECTURE.md) | P1–P10 |
| R21 | Synthetic fixtures, invariant tests, drift and regression coverage | [Testing](TESTING_STRATEGY.md) | P1–P10 |
| R22 | Evidence-based external claims and regulatory/UI/banking blockers | [Research index](../README.md#research-boundaries) | P0/P10 |
| R23 | Documentation review, decisions, phase gates and stop after planning | [Roadmap](ROADMAP.md) | P0 |

## Success measures

Mandatory correctness gates: no unexplained approved reconciliation residual; no unhandled blocking review items; no untraceable material manifest values; no duplicate posting from re-import; no submission without current approval. These are distinct from bank coverage and cannot substitute for it.

Measure import coverage by account/period, review backlog/age, correction rate, transfer false positives, missing evidence, time spent reviewing, and proportion of classifications accepted unchanged. Establish automation-rate targets only after representative synthetic and private evaluation; do not promise a percentage now.

## Human input policy

Ask once for account ownership, applicability, opening balances, and repeatable classification policies, then reuse versioned confirmations within their scope. Ask again only for conflict, changed circumstances, missing evidence, or expiry. Material tax ambiguity, manifest approval, and final submission remain explicit human decisions. Evidence gaps must not be hidden to reduce interaction counts.
