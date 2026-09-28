# Assets and liabilities

Subledgers explain the canonical journal; they are not independent totals added to it. Each lifecycle event references journal/evidence IDs and feeds a reproducible closing projection.

## Opening positions

Import TY2026 filed closing positions with their source fields and acknowledgement where available. Separately establish the economically supported position at 2026-07-01. Differences are reviewed and preserved; do not rewrite the prior return or use an unexplained opening-equity adjustment to conceal them.

Opening journal entries use a documented opening-equity account and a verified position schedule. Unknown basis, ownership, or prior figures remain explicit provisional facts and close blockers where applicable. Bank cash balances are represented once even if they also appear in a Wealth Statement asset schedule.

## Asset lifecycle

States: proposed, active, partially_disposed, disposed, transferred_out. Events include opening, acquisition, capital addition, ownership transfer in/out, partial/full disposal, supported basis adjustment and closing snapshot. Keep acquisition/disposal dates, ownership share, quantity/units where relevant, counterparty, consideration, transaction costs and funding links.

Keep separate values for acquisition cost, tax basis, wealth-reporting basis, market valuation with date/source, and proceeds. Rules decide which enters each tax/wealth field. A market-value observation does not automatically change book wealth or taxable gain.

An acquisition exchanges cash for an asset; it is not automatically personal expenditure. Disposal removes the supported carrying basis, records proceeds and any gain/loss components, and later applies tax treatment. Improvements versus repairs require classification evidence. Noncash gifts/inheritance and ownership transfers require source-of-funds and legal-treatment review; do not fabricate a bank event.

Synthetic example: acquire an asset for 100,000 cash, then dispose for 120,000. Book cash rises by 20,000 over the round trip; only supported gain/other applicable components enter the wealth bridge. Treating all 120,000 as income while also retaining the asset duplicates wealth.

## Liability lifecycle

States: proposed, active, partially_repaid, settled, refinanced, forgiven. Events include opening, drawdown, principal repayment, interest/fees, refinance, forgiveness, transfer and closing snapshot. Track lender, currency, principal, terms evidence, due dates when known and settlement evidence.

Drawdown increases cash and liability; principal repayment reduces both. Neither automatically changes net wealth or income/expenditure. Interest/fees are separate economic events. Refinance settles/links the old liability and opens the new one without duplicating cash movements. Forgiveness changes net wealth but requires explicit tax treatment before filing.

Credit-card borrowing and repayments follow the same separation: purchases establish expenses/assets, payment of the card liability must not expense them again. Accrued versus paid components are tracked separately when supported and applicable.

## Controls

Each asset/liability closes from opening plus supported lifecycle changes using its applicable basis; negative quantities/principal, excessive disposal, missing ownership, unsupported basis changes and mismatches with lender/investment statements create reviews. Snapshots record the calculation and input revisions.

Period-end confirmations may be necessary even when transactions are fully imported. See [Reconciliation](RECONCILIATION.md) for coverage and approval gates, and [Tax engine](TAX_ENGINE.md) for rule-driven valuation.
