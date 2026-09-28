# Security, storage, backup, and recovery

## Private boundary

Threats include accidental Git publication, device/backup loss, cloud disclosure, malicious documents, leaked browser sessions, debug logs, and corruption. Local administration or a compromised unlocked operating system can still access data; encryption and application audit logs are not protection against every local attacker.

Place all real-data databases, document objects, staging files, OCR results, AI caches, reports, manifests, browser profiles and diagnostic artifacts under a separately configured encrypted private root outside the repository and outside ordinary sync folders. Restrict filesystem access to the user. Keep application code and deliberately synthetic tests in Git.

Before real-data use, a storage capability check must verify resolved paths, reject repository/sync-root placement, verify the chosen encryption boundary is mounted/configured, and perform a safe recovery test. Until then, run only synthetic data. Choosing and validating the encryption provider is a Phase 1 research gate; do not invent custom cryptography. All scratch/output paths must obey the boundary. Document any unavoidable OS/browser cache exposure before enabling that component.

## Secrets and browser state

Use the operating-system credential facility for application OAuth/API secrets when integrations are enabled. Store no secrets in SQLite configuration, source files or logs. Do not collect bank credentials. Prefer human IRIS login; any approved retained session is private, encrypted, expiry-controlled and excluded from diagnostic captures. OTPs and CAPTCHA responses are never persisted.

## AI and document handling

Local extraction is the default. Cloud AI is disabled until the user explicitly selects a provider and approves the data classes, minimization, retention/training terms, region considerations and revocation controls. Unknown provider retention is a blocker to enabling it. Keep a disclosure audit containing metadata about what was sent, not a second plaintext payload log.

Redact/minimize identifiers and unnecessary text, but disclose that amounts/narratives may remain identifying. Cloud failure must not prevent local ledger access. Model outputs are untrusted proposals, never executable commands or filing authority.

Treat PDFs, spreadsheets, filenames, OCR and model responses as untrusted input. Disable macros/external references; constrain extraction resources; do not follow instructions embedded in documents. Validate file signatures and sizes. Do not execute downloaded files as parsers.

## Git and logs

The root ignore file excludes common private formats, databases and runtime folders, with explicit synthetic-fixture exceptions. It cannot detect a CNIC pasted into Markdown or a secret renamed to an allowed extension. Before staging/publication, inspect filenames and contents, hidden metadata in future binary fixtures, and the exact staged diff. Synthetic fixtures must be constructed, not merely lightly redacted real documents.

Operational logs contain opaque IDs/codes/counts, not amounts, account details, narratives, tokens or OCR. Detailed audit records live only in the private database. Crash reports, screenshots and tracing are off by default for real-data sessions; any authorized capture stays private and is scrubbed before sharing.

## Backup and restore

After changes, create a daily consistent snapshot; also snapshot before migrations and filing approval/submission. Back up the database with a consistent database snapshot mechanism, not by copying a live DB while ignoring its WAL. Include all referenced immutable documents, schema version, configuration needed for recovery, content hashes, rule/mapping versions and audit/filing history.

Encrypt archives before copying off the private volume. Maintain at least one independent offline or otherwise separately protected copy; optional Drive archives are an additional destination, not the only copy. Keep a recovery key outside the device and backup archive in a user-controlled secure location. Validate key recovery without publishing the key. Never sync a live database.

Operational targets: at most one day of data loss under daily backup and restoration within one working day; these are design targets until measured. Quarterly and before filing, restore into an isolated encrypted directory, verify hashes and foreign keys, reconcile snapshot totals, and compare a manifest hash. A checksum-only check is not a restore drill.

Default until legal retention is established: no automatic pruning of original evidence, filed artifacts, accepted history or backups containing their only surviving copies. Record storage growth and obtain a documented retention policy before introducing deletion. Statutory retention duration, exceptions for pending proceedings and cloud/privacy obligations require authoritative research; do not assume a fixed number of years.

## Migrations and incidents

Migrations are ordered/versioned, reject unknown future schema versions, take a verified pre-migration snapshot, and use transactions where supported. Validate document references and journal invariants afterwards. On failure, preserve diagnostics, stop writes and restore the snapshot; do not promise arbitrary reverse migrations.

For suspected publication or secret exposure: stop publication, revoke affected secrets, identify exactly what escaped, and follow an explicit remediation plan. Deleting a current file does not remove Git history. History rewriting or remote deletion requires scoped authorization. Do not hide incidents by overwriting audit records.
