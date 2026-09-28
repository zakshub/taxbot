# Taxbot

Planning foundation for continuously preparing one resident individual's Pakistan income tax return and Wealth Statement, starting with **Tax Year 2027: 1 July 2026 to 30 June 2027**.

**Status: Phase 0 documentation complete; planning review pending. No application is implemented. Do not start Phase 1 until the planning has been reviewed and implementation is explicitly requested.**

Taxbot is intended to turn financial evidence into a traceable financial ledger, continuously reconcile wealth, apply independently versioned Pakistan tax rules, and produce an approved Filing Manifest. A later assisted IRIS adapter will enter and verify that manifest. Final submission always requires separate human approval.

## Reading order

1. [Product requirements and vision](docs/PRODUCT_REQUIREMENTS.md) — scope and requirement-to-phase coverage.
2. [Architecture](docs/ARCHITECTURE.md) and [data model](docs/DATA_MODEL.md) — boundaries, contracts, identities, and invariants.
3. [Ingestion](docs/INGESTION.md) and [matching](docs/MATCHING_ENGINE.md) — statements, documents, confidence, and review.
4. [Assets and liabilities](docs/ASSETS_AND_LIABILITIES.md) and [reconciliation](docs/RECONCILIATION.md) — lifecycles, continuous checks, and year closing.
5. [Tax engine](docs/TAX_ENGINE.md) and [IRIS automation](docs/IRIS_AUTOMATION.md) — Shadow IRIS, manifest, approvals, and assisted filing.
6. [Security](docs/SECURITY.md) and [testing strategy](docs/TESTING_STRATEGY.md) — storage, recovery, synthetic scenarios, and readiness.
7. [Decisions](docs/DECISIONS.md) and [roadmap / planning status](docs/ROADMAP.md) — accepted defaults, unresolved questions, and next milestone.
8. Research: [FBR](research/FBR.md), [IRIS](research/IRIS.md), [Pakistan banking](research/PAKISTAN_BANKING.md).

Vision is consolidated into product requirements. Workflows live with their owning subsystem; there are no separate VISION or WORKFLOWS files to keep synchronized.

## Operating assumptions

- One taxpayer, one Windows PC; Python and SQLite are the planned baseline, not installed dependencies.
- The structured ledger is authoritative. Excel and Google Sheets are review/export projections.
- Local-first processing; cloud AI requires explicit opt-in and minimized disclosure.
- CSV, Excel, and PDF imports are the baseline. Personal banking APIs and current FBR integration access are not assumed.
- Real financial data belongs in a separately configured encrypted private store outside this repository.
- GitHub contains code when later authorized, documentation, public rule references, tests, and intentionally synthetic fixtures only.

No setup or run commands exist yet. Do not install a framework or create application scaffolding to complete Phase 0.

## Research boundaries

Research was performed on **2026-09-28**. CONFIRMED means supported only within the cited source's scope; LIKELY means an inference; UNKNOWN means not established. No tax rates, current IRIS field codes, or usable personal API access are certified by this planning pack. Publication listings are not validated rule implementations.
