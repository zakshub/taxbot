# Taxbot

Planning foundation for continuously preparing one resident individual's Pakistan income tax return and Wealth Statement, starting with **Tax Year 2027: 1 July 2026 to 30 June 2027**.

**Status: Phase 0 and the bounded Phase 1 canonical-ledger foundation are complete and acceptance-reviewed. Real-data mode remains fail-closed until a separate BitLocker-protected root and verified restore receipt exist. Do not start Phase 2 until explicitly authorized.**

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

- One taxpayer, one Windows PC; Python 3.13 and SQLite from the Python standard library are the implemented baseline.
- The structured ledger is authoritative. Excel and Google Sheets are review/export projections.
- Local-first processing; cloud AI requires explicit opt-in and minimized disclosure.
- CSV, Excel, and PDF imports are the baseline. Personal banking APIs and current FBR integration access are not assumed.
- Real financial data belongs in a separately configured encrypted private store outside this repository.
- GitHub contains code when later authorized, documentation, public rule references, tests, and intentionally synthetic fixtures only.

## Phase 1 commands

No third-party runtime dependencies or framework installation are required.

```powershell
python -m unittest discover -s tests -v
python -m taxbot --root C:\path\to\synthetic-store --mode synthetic init
python -m taxbot --root C:\path\to\synthetic-store --mode synthetic status
```

Real-data bootstrap is deliberately stricter: create a private directory outside the repository and ordinary sync folders on a fully encrypted BitLocker volume; run `init`, `backup`, and `restore-drill` with `--mode real`; then `status` will open real-data mode only after the restore receipt exists. Keep the BitLocker recovery key separately protected. Do not place real taxpayer data in a synthetic store.

The CLI intentionally exposes only storage setup, redacted status, consistent backup and isolated restore-drill operations. Phase 1 ledger commands are an internal Python API pending product workflow design. No frontend, bank parser, tax calculation, AI, or IRIS automation exists.

## Research boundaries

Research was performed on **2026-09-28**. CONFIRMED means supported only within the cited source's scope; LIKELY means an inference; UNKNOWN means not established. No tax rates, current IRIS field codes, or usable personal API access are certified by this planning pack. Publication listings are not validated rule implementations.
