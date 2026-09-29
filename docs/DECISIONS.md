# Decision record

Recorded 2026-09-28. These defaults do not authorize work beyond the current boundary in AGENTS.md. Changes require a dated decision and impact assessment of dependent documents/approvals.

| ID | Decision | Rationale / consequence |
|---|---|---|
| D01 | One resident individual, one Windows PC | User selected; no SaaS/tenant infrastructure; reassess residency each tax year |
| D02 | Python modular monolith and SQLite baseline | Small local deployment; internal contracts before any public API or frontend |
| D03 | Balanced journal with immutable observations and append-only corrections | Explain cash/asset/liability movement; avoid full event sourcing while retaining history |
| D04 | Ledger + referenced immutable document objects are canonical | Spreadsheets, AI outputs and IRIS drafts are projections/proposals |
| D05 | Exact decimal money; original and PKR values retained | Prevent rounding drift and support explicit FX/tax conversion policies |
| D06 | Same-owner transfers require ownership evidence | Similar names/amounts cannot safely establish income exclusion |
| D07 | Local-first extraction, cloud AI opt-in | User preference; provider privacy review is required before disclosure |
| D08 | Confidence and verification are separate axes | High score cannot certify facts or legal treatment |
| D09 | File imports before bank integrations | Usable personal APIs unverified; no bank credentials or payment initiation |
| D10 | Tax rules, semantic return, field mapping and browser adapter remain separate | Rules/UI change independently; browser never determines tax values |
| D11 | Immutable manifest approval plus separate submission approval | Changes invalidate authorization; entry is not permission to submit |
| D12 | Minimal evidence storage, audit and secure-storage contract start in P1 | Later phases depend on provenance; P4 adds extraction/matching breadth |
| D13 | Private encrypted storage outside Git; synthetic-only until verified | Ignore rules are insufficient; encryption provider selection is gated research |
| D14 | Optional Drive archive/source and Sheets review adapters | No live DB synchronization; stale spreadsheet edits become rejected proposals |
| D15 | Initial AI auto-acceptance disabled; <0.90 routes as low confidence | Conservative uncalibrated default; deterministic scoped rules can reduce review |
| D16 | Seven-day default transfer candidate window, exact principal matching | Search heuristic only; unusual dates/FX/splits require evidence and review |
| D17 | Vision merged into requirements; workflows owned by subsystems | Avoid duplicated specifications and keep traceability |
| D18 | No numerical tax rates or guessed IRIS codes in Phase 0 | Listings and historical docs do not establish executable current rules |
| D19 | Windows BitLocker is the Phase 1 real-data volume gate | Native status must report fully encrypted with protection on; root must be outside Git/sync folders and a verified restore receipt is required before data commands |
| D20 | Meezan PKR current salaried searchable-PDF statements are the first Phase 2 format target | Authorized 2026-09-29; implement bank-neutral controls first, then create a bank adapter only from the privately observed structure represented by constructed synthetic fixtures; Faysal is a later source |

## Deferred decisions with gates

| Question | Required evidence / owner | Gate and fallback |
|---|---|---|
| Which private storage encryption provider? | Maintainer evaluates Windows compatibility, scratch coverage and recovery; taxpayer controls keys | Before any real-data use; synthetic-only until resolved |
| What is the exact Meezan searchable-PDF layout/version? | Taxpayer supplies only the structural header/column pattern through a privacy-safe workflow; maintainer constructs an invented fixture | Before claiming Meezan parser support or completing P2; bank-neutral ingestion may proceed, but unknown layouts quarantine |
| Which income/asset categories actually apply? | Taxpayer private onboarding plus authoritative rule research | Before P7 coverage sign-off; unsupported cases block approval |
| Is TY2026 baseline complete and consistent? | Filed documents/acknowledgements and account/asset evidence, reviewed privately | Before closing/approval; provisional opening positions remain flagged |
| Is any cloud AI provider acceptable? | User consent plus provider privacy/retention review | Before enabling cloud; local/manual proposals remain available |
| Are API/ADX or assisted browser access supported now? | Current FBR documentation/support and authorized inspection | Before P9 live use; manual manifest entry remains available |
| Are retention and tax interpretations sufficient? | Authoritative legal sources and qualified review where ambiguity remains | Before rule approval or automatic deletion; no guessed treatment/pruning |

These are intentionally unresolved external/product inputs, not hidden decisions for an implementer. The implementer must stop at the named gate or use the documented fallback. Phase 1 does not depend on current IRIS access or a selected bank.
