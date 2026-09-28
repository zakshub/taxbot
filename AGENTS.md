# Repository instructions

## Current authorization boundary

This repository is in Phase 0. Maintain planning documents only until the user reviews the planning and explicitly authorizes implementation. Do not start Phase 1, build a UI, install frameworks, create parsers, or automate IRIS as part of planning maintenance.

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

For documentation changes, verify links, requirement coverage, financial scenarios, approval boundaries, and contradictions. No application tests or dependency installation are needed for a documentation-only change. Once implementation is authorized, use docs/TESTING_STRATEGY.md and the applicable phase acceptance gate.

Do not force-push, rewrite remote history, or include unrelated files. Stop at the authorized phase boundary.
