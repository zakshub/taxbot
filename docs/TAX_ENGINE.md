# Pakistan tax engine, Shadow IRIS, and Filing Manifest

## Tax rules are a separate subsystem

The financial ledger describes what happened. Pakistan rules determine legal category, taxable base, exemptions, rates, credits, withholding treatment, valuation, period and return presentation. A generic category such as bank profit does not itself establish its final tax treatment.

Initial coverage is selected from the resident individual's actual applicability checklist. Unsupported business, foreign, joint-ownership or unusual-instrument cases remain recordable but block complete return approval. Do not silently exclude an applicable income source to fit the implemented rules.

## Rule package contract

Each immutable package identifies tax year, semantic version, effective date ranges, jurisdiction, source documents/sections and publication dates, retrieval dates, source hashes when available, applicability conditions, calculations, rounding, required facts and tests. Status: draft, under_review, approved, superseded. Store reviewer, evidence and approval time.

An approved package contains only supported rules. An enacted amendment within a tax year creates a new package; historical runs remain reproducible. A new tax year requires explicit applicability review rather than copying previous rates. Finance bills and budget proposals are not enacted rules; explanatory rate cards are aids and must be checked against governing law and applicable amendments.

Unknown source, unclear legal effect or missing facts returns `unsupported`/`needs_review`, not zero. Tax results contain exact intermediate amounts, inputs, formula/rule IDs, version, and final rounding. AI may suggest research or classification, not authoritatively determine tax liability.

## Withholding and tax components

Keep separately: observed deduction, tax section/type if established, gross payment base, period, deductor, evidence, eligibility to claim, applicable credit/adjustment and treatment as adjustable/final/minimum or another legally supported category. Do not treat all withheld amounts as refunds or universally deductible credits.

Link certificates, bank debits, employer schedules and available FBR information as corroborating sources to the same claim. Resolve discrepancies before approval. Prevent the same deduction being claimed twice across documents or sections. Payment receipts and withholding are separate evidence types.

## Shadow IRIS

Shadow IRIS is a versioned semantic return object, independent of browser layout. It contains profile/applicability, income schedules, deductions/credits where supported, tax computations, assets, liabilities, personal expenditure, wealth bridge, required declarations, validation results and lineage.

Represent repeatable rows by stable IDs. Missing, zero and not_applicable are distinct states. All mandatory applicable fields must be resolved; a partial supported return cannot claim completeness. Semantic schema changes have explicit migrations and compatibility checks.

Mapping records specify semantic path/row identity, tax year, form/version, verified target field identity, data type, precision/rounding, prerequisites, entry versus IRIS-computed mode, and evidence of mapping verification. Do not invent codes. Selector details live in the browser adapter. Required declarations or attachments are identified explicitly, never checked or fabricated automatically.

## Manifest contract (no executable schema yet)

The canonical payload includes:

- Manifest schema version, ID, taxpayer reference, tax year/period and generation time.
- Ledger snapshot/revision and evidence dependency digest.
- Tax rule package, semantic schema, field mapping, validation and rounding versions.
- Field/schedule entries: semantic identity, verified target identity, exact canonical value/currency, encoded entry value or expected computed value, source/calculation references.
- Reconciliation/coverage summary, validation results, required human declarations and outstanding nonblocking notes.

Serialize with deterministic key ordering, UTF-8 and canonical decimal strings; hash the complete payload with SHA-256, excluding the hash field and separate approvals. Arrays use explicitly defined stable ordering. Once issued, the payload is immutable. A changed payload is a new manifest with a new hash.

Manifest approval stores actor, time, hash, purpose and referenced validation result. This is local audit evidence, not a claim of a legally qualified digital signature. Verification precedes approval and approval precedes entry. Final submission authorization is separate and scoped to the manifest plus successful read-back of the current draft.

Approval blockers: incomplete applicable coverage, unresolved material evidence/ownership/tax questions, unverified relevant baseline, unsupported rules/mappings, reconciliation failure, unaccounted rounding discrepancy, or stale dependencies. No global 'accept all warnings' bypass is allowed.

## Regulatory maintenance

Revalidate authoritative legislation, amendments, notifications, return schema and deadlines before rule approval and again before filing. Record effective dates separately from discovery dates. If rules change after approval, recompute and show differences for renewed review. Maintain the open research register in [FBR](../research/FBR.md) and [IRIS](../research/IRIS.md); no numeric tax rules are implemented or certified in Phase 0.
