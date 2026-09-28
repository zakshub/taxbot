# Testing strategy

Testing follows the risk: financial identity and arithmetic first, tax boundaries second, integrations last. Phase 0 uses documentation checks only. Later phases use constructed synthetic data until the private storage boundary is verified; real taxpayer files never become fixtures or CI artifacts.

## Fixture policy

Create fixtures from invented institutions, names, account references, descriptions, dates and amounts. Do not anonymize a real statement and call it synthetic. Binary fixtures must be inspected for author, path, thumbnail, revision history and other metadata before commit. Every fixture set includes a `SYNTHETIC.md` statement and the business facts it is designed to test.

Maintain small cases for focused tests and a coherent synthetic TY2027 year for end-to-end checks. Expected results are independently specified rather than copied from implementation output. Keep public fixtures outside the private runtime store and exercise a separate configuration to prove real-data paths fail closed when secure storage is not configured.

## Test layers

| Layer | Required checks |
|---|---|
| Domain/unit | Exact arithmetic, date/tax-year boundaries, state transitions, ownership periods, allocation capacity, rounding and validation errors |
| Database/invariants | Foreign keys, uniqueness, balanced postings, immutable history, revision conflicts, atomic acceptance, migrations and idempotency |
| Adapter contract | Encoding/layout variants, source locators, control totals, malformed/quarantined inputs, unchanged retries and format drift |
| Matching evaluation | Duplicate/transfer candidates, split/FX/fee cases, reversals, recurring suggestions, counterparty ambiguity, confidence calibration and false-positive rates |
| Evidence | Extraction provenance, conflicting facts, many-to-many allocations, certificate/bank corroboration and prevention of double counting |
| Reconciliation | Bank coverage, subledger roll-forward, gross/net components, withholding, missing data and explained/unexplained wealth residuals |
| Tax rules | Legal effective-date and threshold boundaries, applicability, exact intermediates, rounding, unsupported cases and historical reproducibility |
| Shadow IRIS/manifest | Required versus inapplicable values, repeatable schedules, deterministic serialization/hash, lineage and approval invalidation |
| Filing adapter | Mock form drift, save loss/read-before-retry, CAPTCHA/OTP pauses, draft conflict, full read-back, unknown outcome and approval gates |
| Recovery/security | Path escape/symlink resolution where relevant, unconfigured encryption failure, malicious files/formulas, log redaction, backup restore and migration failure |

Use property-based tests where they express genuine invariants: arbitrary accepted journals balance; serializing the same manifest produces the same hash; allocated principal/evidence never exceeds capacity; duplicate command retries never create extra postings. Do not replace example tests with properties when legal boundaries require explicit expected values.

## Mandatory synthetic scenarios

1. Gross salary with withholding and net bank deposit: one income event, no duplicate withholding, filing treatment withheld until a supported rule exists.
2. Same-owner bank transfer with a separate fee, plus a near-identical unrelated payment: transfer principal is excluded from income/expenditure and the unrelated event survives.
3. Two legitimate equal same-day purchases and the same row repeated in an overlapping statement: only the reproduced row becomes duplicate evidence.
4. Loan drawdown, interest, principal repayment and refinance: principal never becomes income/expense and cash/subledger balances agree.
5. Asset acquisition, addition, partial disposal and final disposal: bank movement and lifecycle are not counted twice; value bases remain distinct.
6. Certificate covering several deposits and one withholding debit: allocations reconcile and corroboration does not create another income/tax event.
7. Reversal, delayed transfer leg, FX transfer, split transfer and missing leg: ambiguity stays in review/clearing.
8. Missing account month, undocumented cash withdrawal and missing year-end certificate: a zero wealth residual still fails completeness.
9. Correction after manifest approval and after filing: the first invalidates approval; the second preserves the filed snapshot and creates a revision case.
10. Unknown tax treatment, changed rule package and changed IRIS mapping: approval blocks or stales with an explicit cause.
11. Lost save response and ambiguous submit response: inspect before retry and never resubmit blindly.
12. Spreadsheet formula injection, hostile document instructions, corrupt PDF and oversized input: process safely or quarantine without execution/leakage.

## Phase quality gates

Each roadmap phase must pass its acceptance criteria and relevant regression suite before the next starts. Tests that depend on unverified law or UI are marked blocked, not skipped as passing. Fix flaky tests rather than hiding them with retries. Parser and mapping snapshots may aid review but never auto-update expected behavior without inspecting the semantic diff.

For rule packages, a second reviewer should compare primary sources and worked calculations before approval. For filing readiness, conduct a private dress rehearsal against the current form without final submission, independently compare the manifest and read-back, then perform a restore drill and manual-filing fallback rehearsal.

CI, if later introduced, receives synthetic fixtures only and no production secrets. Network-dependent contract tests are separately gated and do not block local ledger tests when providers are unavailable. Live IRIS tests must never submit and require an explicitly authorized safe scope.

## Phase 0 documentation checks

- All relative Markdown links resolve and public source links use HTTPS where available.
- Requirements R01–R23 have one primary owner and roadmap gate.
- Terms—observation, event, posting, evidence, confidence, verification, rule package, Shadow IRIS, manifest and approvals—are consistent.
- Scenario walkthroughs preserve gross/net, transfer/expense, principal/interest, market/wealth basis and deduction/credit distinctions.
- Research claims include status, source, retrieval date, limitation and consequence.
- Staged content contains no known secrets, private identifiers or application implementation.
