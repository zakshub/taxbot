# Continuous reconciliation and year closing

## Independent checks

Reconciliation is a set of independent controls, not a single green total:

1. Journal: accepted debits equal credits under [money and currency conventions](DATA_MODEL.md).
2. Bank: ledger balances agree with independently sourced statement balances and period coverage.
3. Subledgers: asset/liability opening positions plus lifecycle movements agree with closing positions.
4. Income/expenditure: gross components, net receipts and non-bank facts reconcile without treating transfers or principal as income/expense.
5. Withholding: certificate/transaction/prefill evidence agrees on deductions; eligibility for tax credit is checked separately.
6. Wealth: supported changes in reportable net wealth agree with the applicable inflow/outflow bridge.

Accounting balance alone cannot detect an omitted balanced transaction. Wealth reconciliation alone cannot establish source completeness or legal accuracy.

## Wealth bridge

For an as-of period under the selected reporting basis:

```text
opening_net_wealth = opening_reportable_assets - opening_reportable_liabilities
closing_net_wealth = closing_reportable_assets - closing_reportable_liabilities
net_wealth_change = closing_net_wealth - opening_net_wealth
supported_flow_change = supported_inflows - supported_outflows
unexplained_residual = net_wealth_change - supported_flow_change
```

Inflows/outflows are a rule-derived reconciliation presentation, not all bank credits/debits and not necessarily taxable income. Transfers and exchanges of cash for assets or liability principal generally cancel within net wealth; gifts, noncash movements, valuation differences and tax components require explicit supported bridge treatment. Unknown legal treatment produces a provisional bridge and a blocker, not a guessed category.

Maintain an economic/book bridge before tax rules are available and a separate rule-versioned filing bridge once supported. Never label the former a verified FBR reconciliation. Do not reuse historical codes or generic accounting values as current IRIS mappings.

Synthetic salary example: gross salary 100,000, evidenced withholding 10,000 and net bank deposit 90,000 are components of one salary event. The journal records the 100,000 gross income, 90,000 bank asset and an appropriate 10,000 tax clearing/paid component. The filing bridge must explicitly apply the year's supported treatment of that tax component; it must not use net salary and deduct the same withholding again.

## Cadence and coverage

Recalculate affected checks after accepted imports, corrections, ownership changes, asset/liability events, evidence resolutions and rule updates. Offer monthly review snapshots; no always-on service is needed. Record last input revision, as-of date, currency/basis, rule status and reasons for incompleteness.

Track every expected account and statement interval, opening evidence, unpaired transfers, clearing balances, undocumented cash activity, missing certificates, non-bank events and stale valuations. Cash withdrawals are transfers to a cash account, not proof of expenditure. Cash usage requires evidence or a specifically confirmed supported aggregate; never invent spending to clear a residual.

Display residual causes with linked events and unresolved items. Do not permit a plug labeled miscellaneous expense, gift, or opening balance merely to reach zero. Explicit supported corrections remain possible with evidence and history.

## Tax-year workflow

`open -> closing -> in_review -> approved -> filed`. A reopen before filing returns to open/closing, invalidating approval. Post-filing work creates a revision case with a new snapshot/manifest; original filed records remain immutable. A failed or unknown submission does not set filed.

Closing checklist:

- Validate applicability/residency and supported tax coverage for the year.
- Confirm TY2026 opening reference and separately resolve discrepancies with current supported balances.
- Obtain all expected account periods, year-end balances and applicable certificates.
- Resolve duplicate, transfer, monetary extraction, tax treatment, ownership and evidence blockers.
- Reconcile subledgers, income components and withholding; clear or explicitly resolve all relevant unresolved clearing balances.
- Generate a complete filing bridge and apply explicit field rounding; distinguish rounding differences from unexplained differences. No arbitrary monetary tolerance may erase a discrepancy.
- Freeze the ledger snapshot, calculate with an approved rule package, validate Shadow IRIS and mappings, then request manifest approval.

Approval invalidation is dependency-based: a relevant new document or source conflict, changed accepted fact, rule revision, mapping revision, or rounding policy stales affected results. Irrelevant imports do not rewrite filed history, but relevance must be evaluated and recorded before an existing approval is reused.

FBR's public guidance confirms the reconciliation requirement; it does not supply a complete TY2027 calculation specification. See [FBR research](../research/FBR.md).
