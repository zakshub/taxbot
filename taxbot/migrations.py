"""Ordered SQLite migrations. Migrations are append-only once published."""

from __future__ import annotations


MIGRATIONS: tuple[tuple[int, str, str], ...] = (
    (
        1,
        "phase1_initial",
        r"""
CREATE TABLE schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    applied_at TEXT NOT NULL
);

CREATE TABLE system_state (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    ledger_revision INTEGER NOT NULL CHECK (ledger_revision >= 0)
);
INSERT INTO system_state(singleton, ledger_revision) VALUES (1, 0);

CREATE TABLE taxpayer_profiles (
    id TEXT PRIMARY KEY,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    residency_status TEXT NOT NULL CHECK (residency_status IN ('resident', 'nonresident', 'unknown')),
    private_identifier_ref TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE tax_years (
    id TEXT PRIMARY KEY,
    taxpayer_id TEXT NOT NULL REFERENCES taxpayer_profiles(id),
    label INTEGER NOT NULL CHECK (label >= 2000),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('open', 'closing', 'in_review', 'approved', 'filed')),
    created_at TEXT NOT NULL,
    UNIQUE(taxpayer_id, label),
    CHECK (start_date <= end_date)
);

CREATE TABLE financial_accounts (
    id TEXT PRIMARY KEY,
    taxpayer_id TEXT NOT NULL REFERENCES taxpayer_profiles(id),
    institution TEXT NOT NULL,
    account_kind TEXT NOT NULL,
    currency TEXT NOT NULL,
    private_identifier_ref TEXT,
    status TEXT NOT NULL CHECK (status IN ('active', 'closed')),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    created_at TEXT NOT NULL
);

CREATE TABLE account_ownership (
    id TEXT PRIMARY KEY,
    financial_account_id TEXT NOT NULL REFERENCES financial_accounts(id),
    owner_ref TEXT NOT NULL,
    share_numerator INTEGER NOT NULL CHECK (share_numerator > 0),
    share_denominator INTEGER NOT NULL CHECK (share_denominator > 0),
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    evidence_document_id TEXT REFERENCES documents(id),
    review_status TEXT NOT NULL CHECK (review_status IN ('accepted', 'user_confirmed', 'verified')),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    created_at TEXT NOT NULL,
    CHECK (share_numerator <= share_denominator),
    CHECK (effective_to IS NULL OR effective_from <= effective_to)
);

CREATE TABLE ledger_accounts (
    id TEXT PRIMARY KEY,
    taxpayer_id TEXT NOT NULL REFERENCES taxpayer_profiles(id),
    code TEXT NOT NULL,
    name TEXT NOT NULL,
    account_class TEXT NOT NULL CHECK (account_class IN ('asset', 'liability', 'equity', 'income', 'expense', 'clearing')),
    currency_policy TEXT NOT NULL,
    financial_account_id TEXT REFERENCES financial_accounts(id),
    revision INTEGER NOT NULL CHECK (revision >= 1),
    created_at TEXT NOT NULL,
    UNIQUE(taxpayer_id, code),
    UNIQUE(financial_account_id)
);

CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL UNIQUE CHECK (length(sha256) = 64),
    object_relpath TEXT NOT NULL UNIQUE,
    mime_type TEXT NOT NULL,
    byte_length INTEGER NOT NULL CHECK (byte_length >= 0),
    document_kind TEXT NOT NULL,
    received_at TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE journal_entries (
    id TEXT PRIMARY KEY,
    taxpayer_id TEXT NOT NULL REFERENCES taxpayer_profiles(id),
    effective_date TEXT NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT,
    provenance_method TEXT NOT NULL CHECK (provenance_method IN ('machine_proposed', 'rule_derived', 'user_supplied')),
    review_status TEXT NOT NULL CHECK (review_status IN ('accepted', 'user_confirmed', 'verified')),
    ledger_revision INTEGER NOT NULL UNIQUE CHECK (ledger_revision >= 1),
    correction_of TEXT REFERENCES journal_entries(id),
    reverses_entry_id TEXT REFERENCES journal_entries(id) UNIQUE,
    created_at TEXT NOT NULL
);

CREATE TABLE postings (
    id TEXT PRIMARY KEY,
    journal_entry_id TEXT NOT NULL REFERENCES journal_entries(id),
    ledger_account_id TEXT NOT NULL REFERENCES ledger_accounts(id),
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    direction TEXT NOT NULL CHECK (direction IN ('debit', 'credit')),
    currency TEXT NOT NULL,
    amount_minor INTEGER NOT NULL CHECK (amount_minor >= 0),
    functional_currency TEXT NOT NULL CHECK (functional_currency = 'PKR'),
    functional_minor INTEGER NOT NULL CHECK (functional_minor >= 0),
    UNIQUE(journal_entry_id, ordinal)
);

CREATE TABLE journal_evidence_links (
    id TEXT PRIMARY KEY,
    journal_entry_id TEXT NOT NULL REFERENCES journal_entries(id),
    document_id TEXT NOT NULL REFERENCES documents(id),
    role TEXT NOT NULL CHECK (role IN ('establishes', 'corroborates', 'contradicts', 'explains_component')),
    source_locator TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(journal_entry_id, document_id, role, source_locator)
);

CREATE TABLE audit_events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT NOT NULL UNIQUE,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NOT NULL,
    before_revision INTEGER,
    after_revision INTEGER,
    reason TEXT,
    run_id TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE idempotency_records (
    command_key TEXT PRIMARY KEY,
    command_type TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    result_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_tax_years_taxpayer ON tax_years(taxpayer_id);
CREATE INDEX idx_financial_accounts_taxpayer ON financial_accounts(taxpayer_id);
CREATE INDEX idx_ownership_account_dates ON account_ownership(financial_account_id, effective_from, effective_to);
CREATE INDEX idx_ledger_accounts_taxpayer ON ledger_accounts(taxpayer_id);
CREATE INDEX idx_journal_taxpayer_date ON journal_entries(taxpayer_id, effective_date);
CREATE INDEX idx_postings_journal ON postings(journal_entry_id);
CREATE INDEX idx_evidence_journal ON journal_evidence_links(journal_entry_id);

CREATE TRIGGER immutable_documents_update BEFORE UPDATE ON documents
BEGIN SELECT RAISE(ABORT, 'documents are immutable'); END;
CREATE TRIGGER immutable_documents_delete BEFORE DELETE ON documents
BEGIN SELECT RAISE(ABORT, 'documents are immutable'); END;
CREATE TRIGGER immutable_journal_update BEFORE UPDATE ON journal_entries
BEGIN SELECT RAISE(ABORT, 'journal entries are immutable'); END;
CREATE TRIGGER immutable_journal_delete BEFORE DELETE ON journal_entries
BEGIN SELECT RAISE(ABORT, 'journal entries are immutable'); END;
CREATE TRIGGER immutable_postings_update BEFORE UPDATE ON postings
BEGIN SELECT RAISE(ABORT, 'postings are immutable'); END;
CREATE TRIGGER immutable_postings_delete BEFORE DELETE ON postings
BEGIN SELECT RAISE(ABORT, 'postings are immutable'); END;
CREATE TRIGGER immutable_evidence_update BEFORE UPDATE ON journal_evidence_links
BEGIN SELECT RAISE(ABORT, 'evidence links are immutable'); END;
CREATE TRIGGER immutable_evidence_delete BEFORE DELETE ON journal_evidence_links
BEGIN SELECT RAISE(ABORT, 'evidence links are immutable'); END;
CREATE TRIGGER immutable_audit_update BEFORE UPDATE ON audit_events
BEGIN SELECT RAISE(ABORT, 'audit events are immutable'); END;
CREATE TRIGGER immutable_audit_delete BEFORE DELETE ON audit_events
BEGIN SELECT RAISE(ABORT, 'audit events are immutable'); END;
CREATE TRIGGER immutable_idempotency_update BEFORE UPDATE ON idempotency_records
BEGIN SELECT RAISE(ABORT, 'idempotency records are immutable'); END;
CREATE TRIGGER immutable_idempotency_delete BEFORE DELETE ON idempotency_records
BEGIN SELECT RAISE(ABORT, 'idempotency records are immutable'); END;
""",
    ),
    (
        2,
        "phase2_statement_ingestion_core",
        r"""
CREATE TABLE import_batches (
    id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(id),
    financial_account_id TEXT NOT NULL REFERENCES financial_accounts(id),
    adapter_id TEXT NOT NULL,
    adapter_version TEXT NOT NULL,
    extractor_id TEXT NOT NULL,
    extractor_version TEXT NOT NULL,
    configuration_digest TEXT NOT NULL CHECK (length(configuration_digest) = 64),
    run_key TEXT NOT NULL UNIQUE,
    input_digest TEXT NOT NULL CHECK (length(input_digest) = 64),
    state TEXT NOT NULL CHECK (state IN (
        'received', 'quarantined', 'extracting', 'normalized',
        'validated', 'ready', 'accepted', 'failed'
    )),
    statement_start TEXT,
    statement_end TEXT,
    currency TEXT,
    opening_balance_minor INTEGER,
    closing_balance_minor INTEGER,
    total_debits_minor INTEGER,
    total_credits_minor INTEGER,
    control_status TEXT NOT NULL CHECK (control_status IN ('pending', 'passed', 'failed')),
    layout_signature TEXT NOT NULL,
    diagnostic_code TEXT,
    revision INTEGER NOT NULL CHECK (revision >= 1),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    CHECK (statement_start IS NULL OR statement_end IS NULL OR statement_start <= statement_end)
);

CREATE TABLE import_batch_checkpoints (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    id TEXT NOT NULL UNIQUE,
    batch_id TEXT NOT NULL REFERENCES import_batches(id),
    state TEXT NOT NULL,
    diagnostic_code TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE extraction_runs (
    id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL REFERENCES import_batches(id),
    document_id TEXT NOT NULL REFERENCES documents(id),
    extractor_id TEXT NOT NULL,
    extractor_version TEXT NOT NULL,
    configuration_digest TEXT NOT NULL CHECK (length(configuration_digest) = 64),
    status TEXT NOT NULL CHECK (status IN ('succeeded', 'quarantined', 'failed')),
    created_at TEXT NOT NULL,
    UNIQUE(batch_id, extractor_id, extractor_version, configuration_digest)
);

CREATE TABLE source_observations (
    id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL REFERENCES import_batches(id),
    extraction_run_id TEXT NOT NULL REFERENCES extraction_runs(id),
    document_id TEXT NOT NULL REFERENCES documents(id),
    source_locator TEXT NOT NULL,
    ordinal INTEGER NOT NULL CHECK (ordinal >= 0),
    raw_json TEXT NOT NULL,
    normalized_json TEXT NOT NULL,
    transaction_date TEXT,
    value_date TEXT,
    narration TEXT NOT NULL,
    bank_reference TEXT,
    direction TEXT NOT NULL CHECK (direction IN ('debit', 'credit', 'unknown')),
    amount_minor INTEGER CHECK (amount_minor IS NULL OR amount_minor > 0),
    running_balance_minor INTEGER,
    currency TEXT NOT NULL,
    extraction_confidence TEXT NOT NULL,
    contextual_fingerprint TEXT NOT NULL CHECK (length(contextual_fingerprint) = 64),
    created_at TEXT NOT NULL,
    UNIQUE(extraction_run_id, source_locator, ordinal)
);

CREATE TABLE published_observations (
    observation_id TEXT PRIMARY KEY REFERENCES source_observations(id),
    batch_id TEXT NOT NULL REFERENCES import_batches(id),
    published_at TEXT NOT NULL
);

CREATE TABLE duplicate_candidates (
    id TEXT PRIMARY KEY,
    left_observation_id TEXT NOT NULL REFERENCES source_observations(id),
    right_observation_id TEXT NOT NULL REFERENCES source_observations(id),
    candidate_kind TEXT NOT NULL CHECK (candidate_kind IN ('overlap_fingerprint', 'bank_reference')),
    reason_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    CHECK (left_observation_id < right_observation_id),
    UNIQUE(left_observation_id, right_observation_id, candidate_kind)
);

CREATE TABLE statement_coverage (
    id TEXT PRIMARY KEY,
    batch_id TEXT NOT NULL UNIQUE REFERENCES import_batches(id),
    financial_account_id TEXT NOT NULL REFERENCES financial_accounts(id),
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    assurance TEXT NOT NULL CHECK (assurance IN ('controlled', 'partial')),
    created_at TEXT NOT NULL,
    CHECK (period_start <= period_end)
);

CREATE INDEX idx_import_batches_account_period
    ON import_batches(financial_account_id, statement_start, statement_end);
CREATE INDEX idx_batch_checkpoints_batch ON import_batch_checkpoints(batch_id, sequence);
CREATE INDEX idx_observations_batch ON source_observations(batch_id, ordinal);
CREATE INDEX idx_observations_fingerprint ON source_observations(contextual_fingerprint);
CREATE INDEX idx_published_batch ON published_observations(batch_id);
CREATE INDEX idx_coverage_account_period
    ON statement_coverage(financial_account_id, period_start, period_end);

CREATE TRIGGER immutable_batch_checkpoint_update BEFORE UPDATE ON import_batch_checkpoints
BEGIN SELECT RAISE(ABORT, 'batch checkpoints are immutable'); END;
CREATE TRIGGER immutable_batch_checkpoint_delete BEFORE DELETE ON import_batch_checkpoints
BEGIN SELECT RAISE(ABORT, 'batch checkpoints are immutable'); END;
CREATE TRIGGER immutable_extraction_run_update BEFORE UPDATE ON extraction_runs
BEGIN SELECT RAISE(ABORT, 'extraction runs are immutable'); END;
CREATE TRIGGER immutable_extraction_run_delete BEFORE DELETE ON extraction_runs
BEGIN SELECT RAISE(ABORT, 'extraction runs are immutable'); END;
CREATE TRIGGER immutable_source_observation_update BEFORE UPDATE ON source_observations
BEGIN SELECT RAISE(ABORT, 'source observations are immutable'); END;
CREATE TRIGGER immutable_source_observation_delete BEFORE DELETE ON source_observations
BEGIN SELECT RAISE(ABORT, 'source observations are immutable'); END;
CREATE TRIGGER immutable_published_observation_update BEFORE UPDATE ON published_observations
BEGIN SELECT RAISE(ABORT, 'published observations are immutable'); END;
CREATE TRIGGER immutable_published_observation_delete BEFORE DELETE ON published_observations
BEGIN SELECT RAISE(ABORT, 'published observations are immutable'); END;
CREATE TRIGGER immutable_duplicate_candidate_update BEFORE UPDATE ON duplicate_candidates
BEGIN SELECT RAISE(ABORT, 'duplicate candidates are immutable'); END;
CREATE TRIGGER immutable_duplicate_candidate_delete BEFORE DELETE ON duplicate_candidates
BEGIN SELECT RAISE(ABORT, 'duplicate candidates are immutable'); END;
CREATE TRIGGER immutable_statement_coverage_update BEFORE UPDATE ON statement_coverage
BEGIN SELECT RAISE(ABORT, 'statement coverage is immutable'); END;
CREATE TRIGGER immutable_statement_coverage_delete BEFORE DELETE ON statement_coverage
BEGIN SELECT RAISE(ABORT, 'statement coverage is immutable'); END;
""",
    ),
)

LATEST_SCHEMA_VERSION = MIGRATIONS[-1][0]
