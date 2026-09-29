# Repository instructions

## Current authorization boundary

Phase 0 and the accepted Phase 1 canonical-ledger foundation are complete. Phase 2 is authorized for a Meezan PKR current salaried account supplied as searchable PDF. Implement the bank-neutral ingestion core and a Meezan adapter only from constructed synthetic fixtures based on a privacy-safe structural inspection. Do not claim Meezan support until the actual layout signature and controls are verified. Faysal remains a later source. Do not start Phase 3 classification/matching, build a UI, install frameworks, implement tax rules or automate IRIS without new authorization.

Read README.md, docs/DECISIONS.md, and docs/ROADMAP.md before changing scope. Preserve requirement identifiers and cross-document terminology. Update the owning document rather than duplicating its specification.

## Data and security invariants

- Never commit real taxpayer identifiers, CNIC, credentials, OTPs, statements, certificates, private evidence, actual filing manifests, browser sessions, or environment secrets.
- Real data, including temporary files and diagnostic artifacts, must stay in an approved encrypted private store outside the checkout. Ignore rules are only defense in depth.
- Fixtures must be constructed synthetically, with no real identifiers, hidden metadata, or copied transaction narratives. Clearly mark them synthetic.
- Inspect the exact staged diff before every publication. Never assume that an ignored extension catches private information in Markdown or code.
- Never print credentials or private financial payloads in logs or tool output.

## Financial and filing invariants

- Exact decimal money only; retain source evidence and correction history.
- Do not equate bank credits with income or bank debits with personal expenditure.
- Same-owner transfers do not create income/expenditure; ownership must be established.
- Confidence is not verification. Unresolved and unsupported items stay visible.
- Keep financial categorization, tax-year rules, semantic return mapping, and browser selectors separate.
- No fabricated balancing adjustments, tax rates, field codes, or missing evidence.
- IRIS automation consumes approved manifests only. Pause for CAPTCHA/OTP; never bypass either. Final submission needs distinct, current human approval.
- A change to relevant evidence, ledger, rules, mapping, or rounding invalidates dependent approval.

## Research and validation

Use authoritative primary sources for external claims. Record retrieval date, applicability, limitations, and CONFIRMED / LIKELY / UNKNOWN status. Do not confuse historic API documentation, payment APIs, or sales-tax APIs with current individual income-tax filing access.

For documentation changes, verify links, requirement coverage, financial scenarios, approval boundaries, and contradictions. For Phase 1 or Phase 2 code changes, run the complete standard-library test suite with ResourceWarning promoted to an error, compile the package, and use the applicable acceptance gate in docs/ROADMAP.md. Do not install dependencies merely to satisfy a check.

Do not force-push, rewrite remote history, or include unrelated files. Stop at the authorized phase boundary.
