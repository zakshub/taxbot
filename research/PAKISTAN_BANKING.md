# Pakistan banking integration research

Research dates: **2026-09-28 and 2026-09-29**. Status vocabulary follows [FBR research](FBR.md). No bank account access or credentials were requested.

| ID / claim | Status / source | Applicability and limitation | Architectural consequence / next verification |
|---|---|---|---|
| B01: SBP strategy discusses developing open banking | CONFIRMED — [National Financial Inclusion Strategy 2024–28](https://www.sbp.org.pk/nfis/nfis2024-28.pdf), reviewed 2026-09-28 | A strategy/pilot framework is not production personal-account API access | No API dependency; check later regulatory releases and bank-specific products if needed |
| B02: Bank Alfalah publishes an API developer portal | CONFIRMED — [developer portal](https://apiportal.bankalfalah.com/bankalfalah/sb/), retrieved 2026-09-28 | Listed products include payments; a portal does not prove retail transaction-history access | Research eligibility, scopes, history and onboarding before proposing a connector |
| B03: Bank Alfalah advertises statement delivery for Premier customers | CONFIRMED — [Premier e-statements](https://www.bankalfalah.com/premier/e-statements/), retrieved 2026-09-28 | Product-specific; source does not verify this user's bank/product, exact file format, or API | User-obtained statements are viable design input; verify actual format privately before P2 |
| B04: Statement downloads can be the initial integration route | LIKELY for a specific user's portfolio — supported by B03 but portfolio unknown | Availability, history length, fees, passwords and export formats vary | File-first design; request bank names and synthetic representative layout before parser selection |
| B05: Universal usable personal read-only transaction API exists | UNKNOWN — no supporting contract established | Payment/Raast/corporate APIs are not equivalent to personal history APIs | Do not promise live sync or design around it |
| B06: Taxpayer's bank formats, unique reference semantics and full-year history | UNKNOWN — private onboarding required | No real statements examined | Confirm selected bank/product and supported synthetic format before P2 acceptance |
| B07: Meezan offers free e-statements for its PKR current account | CONFIRMED — [Meezan Rupee Current Account](https://www.meezanbank.com/rupee-current-account/), retrieved 2026-09-29 | Confirms an e-statement facility for the product family; it does not establish PDF layout, history depth, password behavior, or parser stability | Searchable PDF is the selected file-first route; inspect structure privately and fail closed on unknown signatures |
| B08: Meezan WhatsApp Banking advertises bank-statement download | CONFIRMED — [Meezan Ways to Bank](https://www.meezanbank.com/ways-to-bank/), retrieved 2026-09-29 | Channel availability does not establish the downloaded format or suitability for automated parsing | User obtains the file; Taxbot does not automate bank login, WhatsApp, credentials, or download |
| B09: Meezan searchable-PDF transaction table and reference semantics | UNKNOWN — no authoritative public format specification found on 2026-09-29 | Product/channel revisions may differ; a text layer alone does not prove reliable reading order | Do not create a Meezan parser from assumptions; construct fixtures only after privacy-safe structural inspection |

## Bank capability matrix to complete later

For each actual bank/product, record statement channels, supported CSV/Excel/PDF formats, date/amount conventions, statement frequency, password handling, available history, bank-reference uniqueness, running/opening/closing balances, FX behavior and format versions. API research additionally requires eligibility, read-only permissions, authentication, pricing, rate limits, terms, history depth and revocation. Leave unknown cells UNKNOWN.

User-obtained statements are the baseline. A local watched folder may later reduce clicks, but files must still pass staging and controls. Email ingestion, screen scraping and autonomous bank login are not initial commitments. The project does not request bank credentials or initiate payments.

Format drift fails in quarantine with actionable diagnostics. A bank cannot be called supported based on one successful file; validate overlap, repeated transactions, reversals, month/year boundaries and statement totals using deliberately synthetic fixtures matching the selected layout.
