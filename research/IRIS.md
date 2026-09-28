# IRIS research register

Research date: **2026-09-28**. Status vocabulary follows [FBR research](FBR.md). Public pages were inspected; no taxpayer login, credentials, private return or authenticated automation was used.

| ID / claim | Status / source | Applicability and limitation | Architectural consequence / next verification |
|---|---|---|---|
| I01: IRIS public portal provides login and filing-related help | CONFIRMED — [IRIS portal](https://iris.fbr.gov.pk/), retrieved 2026-09-28 | Public landing page only; it does not establish authenticated automation behavior | Plan user-assisted authentication; inspect authorized current flow before P9 |
| I02: FBR documents Liberated Model API topics/vendor registration and IRIS-ADX | CONFIRMED — [FBR knowledge base](https://help.fbr.gov.pk/), retrieved 2026-09-28 | Historical topics include TY2018 amount codes; current service availability not tested | Do not state that no official API exists; investigate scope and eligibility without designing around access |
| I03: Current personal income-tax API access, enrollment and TY2027 support | UNKNOWN — I02 is an investigation lead, not proof | No usable endpoint contract, credentials, approval or support confirmation obtained | Browser/manual manifest path remains baseline; separate ADR required if an API becomes viable |
| I04: Portal exposes CAPTCHA in public verification functions | CONFIRMED — [IRIS portal](https://iris.fbr.gov.pk/), retrieved 2026-09-28 | Does not prove login or every submission step uses CAPTCHA | Universal human-pause boundary; never bypass any encountered challenge |
| I05: Exact OTP/CAPTCHA/session requirements for TY2027 filing | UNKNOWN — authenticated flow not inspected | These can vary by operation/account/session | Human input and expiry handling required; inspect privately before adapter approval |
| I06: Current TY2027 field identities, calculated fields, save behavior and completion states | UNKNOWN — [IRIS help index](https://e.fbr.gov.pk/SOP/IRIS/help/index.html), retrieved 2026-09-28 | Help exists, but historic guidance cannot establish current form details | Versioned mapping verification and read-back tests are launch gates |
| I07: Automation permissions, restrictions and supported testing environment | UNKNOWN — current terms/support confirmation needed | Public availability is not permission for unattended automation | No live write testing until access conditions and safe testing scope established |
| I08: Draft retention, safe repeated saves and behavior after timeout | UNKNOWN — no authenticated experiment performed | Do not assume idempotent writes/submission | Checkpoints plus read-before-retry; unknown outcomes require inspection |

## Current design implications

The later browser adapter is assisted and constrained to an approved manifest. It is not a tax engine. FBR's general guidance describes successful completion of required forms; the actual current task/status structure must be checked before claiming filing success. No selectors, endpoint guesses or field-code tables are included here.

Do not conflate sales invoicing integration, withholding statement templates, payment services, third-party vendor programs, and an individual annual return API. A publicly listed template does not prove full return import support.

## Verification checklist before Phase 9

Confirm terms and permitted access, current form/year availability, test environment options, legal/applicability mapping, authentication steps, draft conflict handling, save semantics, computed values, zero/not-applicable representation, repeatable schedules, acknowledgement and revised-return behavior. Use a mock adapter first. Any live draft interaction must be explicitly scoped and must not risk accidental submission.

Record observations as dated evidence with sensitive captures kept only in the private store. If current access or UI stability prevents safe automation, keep manual entry/read-back from the approved manifest as the supported fallback. Never bypass a security challenge to meet a roadmap date.
