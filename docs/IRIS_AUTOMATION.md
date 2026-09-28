# Assisted IRIS filing architecture

This is a Phase 9 design, not permission to automate IRIS now. Current-year form details, authenticated flows, supported integration access and automation conditions remain [research gates](../research/IRIS.md).

## Boundary

Input: an immutable validated Filing Manifest, matching human manifest approval, supported adapter/form version and privately established session. Output: draft read-back, discrepancies, run history and, only after separate approval, submission evidence.

The adapter cannot calculate tax, generate substitute values, change classifications, or change the manifest to match the website. IRIS-computed values are observed and compared with manifest expectations. Unexpected values return to the tax/mapping review process.

## Run states

| State | Required behavior |
|---|---|
| preflight | Verify manifest hash/approval/dependencies, taxpayer/year and supported form; refuse stale input |
| authenticating | User completes login as needed; use a dedicated private session |
| human_pause | Explain CAPTCHA/OTP/security interaction; resume only after human completion and session checks |
| inspecting_draft | Read existing draft, identify version and conflicts; never overwrite an unknown return |
| entering_draft | Enter only approved fields; checkpoint logical sections after verifying save/read-back |
| reading_back | Read all relevant entered/computed fields and applicable schedules; normalize only documented display formatting |
| discrepancy | Record exact mismatch privately; stop progression and require corrected upstream review if needed |
| awaiting_submission_approval | Present taxpayer/year, current manifest and complete comparison; ask explicit final authorization |
| submitting | One intentional submission action under current authorization |
| outcome_unknown | Inspect status/receipt through safe reads; never blindly retry submission |
| submitted | Capture acknowledgement and submitted artifact references; verify expected return/wealth completion |
| failed / cancelled | Preserve safe checkpoint; invalidate final authorization on any changed context |

## Authentication and security

Never solve, bypass or outsource CAPTCHA. OTP and security prompts require human handling; do not retain codes, screenshots containing them, or automation traces of entry. Credentials and session material never enter the ledger or Git. Store any permitted reusable session only in the encrypted private boundary, with expiry/logout and cleanup controls.

Pause safely on expiry, rate limits, lockout warnings and unexpected security steps. Do not loop login attempts. Recheck identity, year, manifest/dependency versions and draft state after reauthentication.

## Draft safety and UI drift

Use versioned semantic locators and form checks; do not rely on coordinates alone or silently adapt to unfamiliar controls. Unknown labels, mandatory fields, schedule shapes or calculations stop the run. A changed mapping requires reviewed mapping version and a newly approved manifest, even if the visible change seems minor.

Draft writes must be scoped and read back. When a save response is lost, inspect current state before retrying. Detect pre-existing user edits as conflicts; obtain a resolved draft plan rather than replacing them silently. Checkpoints bind the manifest hash, section identity and observed state, not just 'last clicked button'.

Read-back compares complete applicable values, including zero/not-applicable distinctions and computed fields. Display separators and equivalent formatting may normalize under documented rules; monetary differences cannot be ignored by broad tolerance.

## Human approval boundary

Manifest approval permits entry only. Final submission approval is a distinct action for a current draft with passing read-back and no blockers. Any further draft change, manifest change, identity/year change or uncertain session context invalidates that authorization and requires another review.

After submission, verify acknowledgement/status and preserve the submitted representation privately. A click alone is not evidence of filing. If separate return and Wealth Statement completion is required by the current form, check both; do not assume historical UI task structure persists.

Manual fallback: export the approved manifest and field/evidence checklist for human entry and comparison. It remains usable when UI automation is blocked. FBR API/ADX availability may warrant a future adapter decision, but not an unverified alternate route.
