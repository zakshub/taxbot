# Classification, transfers, and evidence matching

## Decision pipeline

Process duplicate candidates first, then transfer/economic-event candidates, deterministic classification, and finally AI suggestions for unresolved cases. Matching operates on observations and accepted events with their revisions; it cannot bypass canonical acceptance or overwrite user decisions.

Counterparty aliases normalize names/references for candidate generation. A similar name, contact, or family relationship is not proof of account ownership. Recurring patterns suggest category/counterparty and expected evidence; only an observed or explicitly evidenced event creates a journal entry.

## Internal transfers

Match principal between accounts owned by the same taxpayer during the transaction dates. Require established ownership, compatible currencies or documented FX, opposite directions, amount conservation and corroborating reference/date context. Prefer unique supported matches; equal amounts alone are insufficient.

Default candidate window: transaction/value dates within seven calendar days, configurable and versioned per adapter. This is a search window, not proof. Transactions outside it remain searchable/reviewable. Same-currency principal must match exactly after separately evidenced fees; do not hide differences with an arbitrary tolerance.

Handle one-to-many and many-to-one allocations explicitly. A source leg cannot be fully consumed twice. Missing legs create unresolved transfer clearing and coverage alerts. Cross-year transfers preserve the event dates and a supported in-transit position rather than shifting dates to force equality. Joint/partial ownership and foreign-currency transfers require review until a validated policy covers them.

Example: bank A decreases by synthetic PKR 10,100 and bank B increases by 10,000. With fee evidence, post transfer principal 10,000 and expense 100. Without fee evidence, propose the link but leave the difference unresolved. Do not classify the receiving bank credit as income.

## Classification and confidence

Generic categories express economic purpose: salary receipt, bank profit, personal expenditure, transfer, loan principal, interest, asset acquisition/disposal, gift, tax payment, refund, unresolved. Pakistan tax classification is computed later from supported facts and tax-year rules.

Each proposal records confidence in [0,1], confidence kind (heuristic/model/calibrated), reason codes, supporting and contradicting evidence, input revisions and model/prompt or rule version. Missing confidence is unknown, not 1. Model self-reported scores are not calibrated probabilities.

Initial routing defaults: score below 0.90 is low confidence and queues review; score at/above 0.90 is still a proposal. No AI-only automatic acceptance is enabled initially. Deterministic, tested rules explicitly approved by the user can accept categories within their precise scope. Ownership ambiguity, monetary extraction conflict, competing matches, unsupported tax treatment and material missing evidence always queue regardless of score.

Calibrate later on a labeled evaluation set, measuring false transfer/duplicate positives separately from classification accuracy. Change thresholds by versioned policy only after documented evidence; preserve prior decisions. Do not optimize review counts by suppressing uncertainty.

## Review queue

States: open, awaiting_evidence, resolved, dismissed_with_reason, superseded. Priority reflects filing impact and coverage gaps, not only amount. Items show proposed action, alternatives, source locators, confidence and reasons; user actions include accept, correct, split, reject, request evidence, or confirm a repeatable rule.

A decision includes target revision, actor, time and reason/evidence. New source conflicts reopen a new linked review; they do not erase the old resolution. Bulk confirmation must enumerate the affected records and rule scope. Dismissing an item does not waive an underlying filing blocker. Verification is a separate record as defined in [Data model](DATA_MODEL.md).

## Evidence allocation

Use relation roles: establishes, corroborates, contradicts, explains_component. Monetary allocation consumes capacity of a defined evidence claim, not every document link. Multiple documents can corroborate the same withholding claim without doubling its amount; a certificate covering multiple events allocates its total across them.

Check currency, period, remaining capacity, and event allocations. Partial matches remain explicit. Conflicting gross/net amounts create component-level review. Certificates alone may establish supported non-bank facts, but accepting those facts must check for existing events first.

User confirmations and verified deterministic decisions persist until their inputs or scope change. AI provider failure merely leaves proposals pending; the accepted ledger remains usable.
