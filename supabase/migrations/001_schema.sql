-- ============================================================================
-- AGENTBREAK: Supabase Database Migration 001 - Core Schema & Security Views
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS ab;

-- ----------------------------------------------------------------------------
-- 1. ENUMS
-- ----------------------------------------------------------------------------
DO $$ BEGIN
    CREATE TYPE ab.platform_role AS ENUM ('admin', 'security_engineer', 'viewer');
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE ab.surface AS ENUM (
        'instructions', 'memory', 'retrieval', 'tool_permissions', 'multi_step'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE ab.run_kind AS ENUM (
        'live', 'replay', 'rerun', 'validation', 'regression'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE ab.campaign_status AS ENUM (
        'queued', 'running', 'completed', 'failed', 'cancelled', 'interrupted'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE ab.verdict AS ENUM (
        'refused', 'denied', 'partial', 'success', 'error'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE ab.finding_status AS ENUM (
        'open', 'mitigated', 'fixed', 'regressed'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE ab.fix_verdict AS ENUM (
        'fixed', 'partially_mitigated', 'not_fixed', 'fixed_with_regression'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
    CREATE TYPE ab.approval_status AS ENUM (
        'pending', 'approved', 'denied', 'expired'
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- ----------------------------------------------------------------------------
-- 2. IDENTITY & PROFILES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ab.profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID UNIQUE, -- Foreign key to auth.users if available
    display_name TEXT NOT NULL,
    role ab.platform_role NOT NULL DEFAULT 'viewer',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'disabled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 3. TARGETS & VERSIONS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ab.targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    preset_key TEXT UNIQUE,
    current_version_id UUID,
    created_by UUID REFERENCES ab.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ab.target_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_id UUID NOT NULL REFERENCES ab.targets(id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'::jsonb, -- system prompt, tools, memory, rag settings
    manifest JSONB NOT NULL DEFAULT '{}'::jsonb, -- role-based tool access control manifest
    content_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE ab.targets
    ADD CONSTRAINT fk_targets_current_version
    FOREIGN KEY (current_version_id) REFERENCES ab.target_versions(id)
    DEFERRABLE ININITIALLY DEFERRED;

CREATE TABLE IF NOT EXISTS ab.rag_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_version_id UUID NOT NULL REFERENCES ab.target_versions(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    trust TEXT NOT NULL DEFAULT 'untrusted' CHECK (trust IN ('trusted', 'untrusted')),
    docs JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 4. FIXTURES & CANARIES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ab.fixtures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    seed INT NOT NULL,
    version TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ab.canaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fixture_id UUID NOT NULL REFERENCES ab.fixtures(id) ON DELETE CASCADE,
    record_ref TEXT NOT NULL,
    sensitivity TEXT NOT NULL DEFAULT 'high',
    token_hmac TEXT NOT NULL,
    canary_token TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 5. DEFENSE PROFILES & VERSIONS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ab.defense_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    current_version_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ab.defense_profile_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    defense_profile_id UUID NOT NULL REFERENCES ab.defense_profiles(id) ON DELETE CASCADE,
    version TEXT NOT NULL,
    controls JSONB NOT NULL DEFAULT '{}'::jsonb, -- enabled flags + parameters
    determinism JSONB NOT NULL DEFAULT '{}'::jsonb, -- map of control_id -> "D" | "P"
    content_hash TEXT NOT NULL,
    parent_version_id UUID REFERENCES ab.defense_profile_versions(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE ab.defense_profiles
    ADD CONSTRAINT fk_defense_profiles_current_version
    FOREIGN KEY (current_version_id) REFERENCES ab.defense_profile_versions(id)
    DEFERRABLE ININITIALLY DEFERRED;

-- ----------------------------------------------------------------------------
-- 6. CAMPAIGNS & ATTACKS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ab.campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_version_id UUID REFERENCES ab.target_versions(id),
    defense_profile_version_id UUID REFERENCES ab.defense_profile_versions(id),
    mode TEXT NOT NULL DEFAULT 'black' CHECK (mode IN ('white', 'black')),
    surfaces ab.surface[] NOT NULL DEFAULT ARRAY['instructions']::ab.surface[],
    goals JSONB NOT NULL DEFAULT '[]'::jsonb,
    status ab.campaign_status NOT NULL DEFAULT 'queued',
    budget JSONB NOT NULL DEFAULT '{"max_attempts": 10, "max_llm_calls": 50, "max_wall_seconds": 600}'::jsonb,
    llm_calls_used INT NOT NULL DEFAULT 0,
    attempts_used INT NOT NULL DEFAULT 0,
    config_snapshot JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    created_by UUID REFERENCES ab.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ab.attacks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES ab.campaigns(id) ON DELETE CASCADE,
    iteration INT NOT NULL,
    beam_depth INT NOT NULL DEFAULT 1,
    parent_attack_id UUID REFERENCES ab.attacks(id) ON DELETE SET NULL,
    goal TEXT NOT NULL,
    surface ab.surface NOT NULL DEFAULT 'instructions',
    category TEXT NOT NULL,
    strategy TEXT NOT NULL,
    injection_point TEXT NOT NULL DEFAULT 'direct',
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    verdict ab.verdict NOT NULL DEFAULT 'error',
    partial_score DOUBLE PRECISION NOT NULL DEFAULT 0.0 CHECK (partial_score >= 0.0 AND partial_score <= 1.0),
    model_assisted BOOLEAN NOT NULL DEFAULT FALSE,
    best_in_chain BOOLEAN NOT NULL DEFAULT FALSE,
    oracle_verdict JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 7. RUNS, EVENTS & INTEGRITY
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ab.runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attack_id UUID REFERENCES ab.attacks(id) ON DELETE CASCADE,
    kind ab.run_kind NOT NULL DEFAULT 'live',
    target_version_id UUID REFERENCES ab.target_versions(id),
    defense_profile_version_id UUID REFERENCES ab.defense_profile_versions(id),
    fixture_id UUID REFERENCES ab.fixtures(id),
    seed INT NOT NULL DEFAULT 42,
    success BOOLEAN NOT NULL DEFAULT FALSE,
    tool_call_count INT NOT NULL DEFAULT 0,
    llm_calls INT NOT NULL DEFAULT 0,
    head_hash TEXT,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

-- Append-only events table
CREATE TABLE IF NOT EXISTS ab.events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES ab.runs(id) ON DELETE CASCADE,
    seq INT NOT NULL,
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    event_type TEXT NOT NULL,
    actor TEXT NOT NULL DEFAULT 'victim',
    taint TEXT[] NOT NULL DEFAULT ARRAY[]::TEXT[],
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    parent_seq INT,
    prev_hash TEXT NOT NULL,
    hash TEXT NOT NULL,
    CONSTRAINT uq_events_run_seq UNIQUE (run_id, seq)
);

-- Append-only run seals table
CREATE TABLE IF NOT EXISTS ab.run_seals (
    run_id UUID PRIMARY KEY REFERENCES ab.runs(id) ON DELETE CASCADE,
    head_hash TEXT NOT NULL,
    event_count INT NOT NULL,
    seal_hmac TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Append-only model calls table
CREATE TABLE IF NOT EXISTS ab.model_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID REFERENCES ab.runs(id) ON DELETE CASCADE,
    seq INT NOT NULL,
    prompt_hash TEXT NOT NULL,
    prompt JSONB NOT NULL,
    response JSONB NOT NULL,
    model TEXT NOT NULL,
    temperature DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    from_cache BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ab.llm_cache (
    prompt_hash TEXT PRIMARY KEY,
    model TEXT NOT NULL,
    response JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 8. FINDINGS & STANDARDS MAPPING
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ab.findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_version_id UUID NOT NULL REFERENCES ab.target_versions(id) ON DELETE CASCADE,
    root_cause_key TEXT NOT NULL,
    title TEXT NOT NULL,
    surface ab.surface NOT NULL,
    root_cause TEXT NOT NULL,
    impact INT NOT NULL CHECK (impact BETWEEN 1 AND 5),
    exploitability INT NOT NULL CHECK (exploitability BETWEEN 1 AND 5),
    reach INT NOT NULL CHECK (reach BETWEEN 1 AND 5),
    severity_score INT GENERATED ALWAYS AS (impact * exploitability * reach) STORED,
    severity TEXT NOT NULL CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    owasp_id TEXT NOT NULL,
    atlas_id TEXT,
    reliability_k INT NOT NULL DEFAULT 0,
    reliability_n INT NOT NULL DEFAULT 0,
    ci_low DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    ci_high DOUBLE PRECISION NOT NULL DEFAULT 0.0,
    flaky BOOLEAN NOT NULL DEFAULT FALSE,
    model_assisted BOOLEAN NOT NULL DEFAULT FALSE,
    breaking_event_seq INT,
    status ab.finding_status NOT NULL DEFAULT 'open',
    minimized_exploit JSONB,
    mitigation TEXT,
    nist_fields JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_findings_target_root_cause UNIQUE (target_version_id, root_cause_key)
);

CREATE TABLE IF NOT EXISTS ab.finding_evidence (
    finding_id UUID NOT NULL REFERENCES ab.findings(id) ON DELETE CASCADE,
    run_id UUID NOT NULL REFERENCES ab.runs(id) ON DELETE CASCADE,
    event_seq INT NOT NULL,
    PRIMARY KEY (finding_id, run_id, event_seq)
);

CREATE TABLE IF NOT EXISTS ab.attack_corpus (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id UUID NOT NULL REFERENCES ab.findings(id) ON DELETE CASCADE,
    minimized_payload JSONB NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ab.audit_findings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    target_version_id UUID NOT NULL REFERENCES ab.target_versions(id) ON DELETE CASCADE,
    tool TEXT NOT NULL,
    role TEXT NOT NULL,
    granted_scope TEXT NOT NULL,
    intended_scope TEXT NOT NULL,
    gap TEXT NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('Low', 'Medium', 'High', 'Critical')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 9. DEFENSE EVALUATION
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ab.benign_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key TEXT UNIQUE NOT NULL,
    role TEXT NOT NULL,
    prompt TEXT NOT NULL,
    expected_state JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ab.validation_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    finding_id UUID NOT NULL REFERENCES ab.findings(id) ON DELETE CASCADE,
    defense_profile_version_id UUID NOT NULL REFERENCES ab.defense_profile_versions(id) ON DELETE CASCADE,
    check_a JSONB NOT NULL DEFAULT '{}'::jsonb,
    check_b JSONB NOT NULL DEFAULT '{}'::jsonb,
    check_c JSONB NOT NULL DEFAULT '{}'::jsonb,
    verdict ab.fix_verdict NOT NULL DEFAULT 'not_fixed',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ab.eval_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES ab.campaigns(id) ON DELETE CASCADE,
    combo_bits INT NOT NULL CHECK (combo_bits BETWEEN 0 AND 31),
    defense_combo JSONB NOT NULL DEFAULT '[]'::jsonb,
    asr_k INT NOT NULL DEFAULT 0,
    asr_n INT NOT NULL DEFAULT 0,
    benign_pass INT NOT NULL DEFAULT 0,
    benign_total INT NOT NULL DEFAULT 0,
    utility_retention DOUBLE PRECISION NOT NULL DEFAULT 1.0,
    regressions JSONB NOT NULL DEFAULT '[]'::jsonb,
    cached BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ab.regression_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    defense_profile_version_id UUID NOT NULL REFERENCES ab.defense_profile_versions(id) ON DELETE CASCADE,
    summary JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ
);

-- ----------------------------------------------------------------------------
-- 10. GOVERNANCE, APPROVALS & AUDIT LOG
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ab.approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES ab.runs(id) ON DELETE CASCADE,
    event_seq INT NOT NULL,
    tool TEXT NOT NULL,
    args JSONB NOT NULL DEFAULT '{}'::jsonb,
    status ab.approval_status NOT NULL DEFAULT 'pending',
    decided_by UUID REFERENCES ab.profiles(id) ON DELETE SET NULL,
    decided_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ NOT NULL DEFAULT (NOW() + INTERVAL '120 seconds'),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ab.reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    format TEXT NOT NULL CHECK (format IN ('json', 'html', 'pdf')),
    storage_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    created_by UUID REFERENCES ab.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Append-only audit log table
CREATE TABLE IF NOT EXISTS ab.audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    actor UUID REFERENCES ab.profiles(id) ON DELETE SET NULL,
    action TEXT NOT NULL,
    entity TEXT NOT NULL,
    entity_id TEXT,
    ip TEXT,
    ts TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ----------------------------------------------------------------------------
-- 11. STANDARDS LOOKUP TABLES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ab.owasp_llm_categories (
    id TEXT PRIMARY KEY, -- e.g. LLM01:2025
    name TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ab.atlas_techniques (
    id TEXT PRIMARY KEY, -- e.g. AML.T0054
    name TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ab.root_cause_map (
    root_cause_key TEXT PRIMARY KEY,
    owasp_id TEXT NOT NULL REFERENCES ab.owasp_llm_categories(id),
    atlas_id TEXT REFERENCES ab.atlas_techniques(id)
);


-- ----------------------------------------------------------------------------
-- 12. TRIGGERS & FUNCTIONS (Integrity Layer - Domain 10)
-- ----------------------------------------------------------------------------

-- Function: Hash Chain Guard for Events
CREATE OR REPLACE FUNCTION ab.events_guard() RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    last_seq INT;
    last_hash TEXT;
BEGIN
    SELECT seq, hash INTO last_seq, last_hash
    FROM ab.events
    WHERE run_id = NEW.run_id
    ORDER BY seq DESC
    LIMIT 1;

    IF last_seq IS NULL THEN
        IF NEW.seq <> 0 OR NEW.prev_hash <> repeat('0', 64) THEN
            RAISE EXCEPTION 'Event chain for run % must start at seq 0 with prev_hash of 64 zeros', NEW.run_id;
        END IF;
    ELSIF NEW.seq <> last_seq + 1 OR NEW.prev_hash <> last_hash THEN
        RAISE EXCEPTION 'Event chain broken for run % at seq % (expected seq %, prev_hash %)', NEW.run_id, NEW.seq, last_seq + 1, last_hash;
    END IF;
    RETURN NEW;
END $$;

DROP TRIGGER IF EXISTS t_events_guard ON ab.events;
CREATE TRIGGER t_events_guard
    BEFORE INSERT ON ab.events
    FOR EACH ROW EXECUTE FUNCTION ab.events_guard();

-- Function: Append-Only Deny Mutation Trigger
CREATE OR REPLACE FUNCTION ab.deny_mutation() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'Table % is strictly append-only. UPDATE and DELETE are prohibited.', TG_TABLE_NAME;
END $$;

DROP TRIGGER IF EXISTS t_events_ro ON ab.events;
CREATE TRIGGER t_events_ro
    BEFORE UPDATE OR DELETE ON ab.events
    FOR EACH ROW EXECUTE FUNCTION ab.deny_mutation();

DROP TRIGGER IF EXISTS t_run_seals_ro ON ab.run_seals;
CREATE TRIGGER t_run_seals_ro
    BEFORE UPDATE OR DELETE ON ab.run_seals
    FOR EACH ROW EXECUTE FUNCTION ab.deny_mutation();

DROP TRIGGER IF EXISTS t_model_calls_ro ON ab.model_calls;
CREATE TRIGGER t_model_calls_ro
    BEFORE UPDATE OR DELETE ON ab.model_calls
    FOR EACH ROW EXECUTE FUNCTION ab.deny_mutation();

DROP TRIGGER IF EXISTS t_audit_log_ro ON ab.audit_log;
CREATE TRIGGER t_audit_log_ro
    BEFORE UPDATE OR DELETE ON ab.audit_log
    FOR EACH ROW EXECUTE FUNCTION ab.deny_mutation();

-- Function: Wilson 95% Confidence Interval Calculation
CREATE OR REPLACE FUNCTION ab.wilson_ci(k INT, n INT, OUT ci_low DOUBLE PRECISION, OUT ci_high DOUBLE PRECISION)
LANGUAGE plpgsql IMMUTABLE AS $$
DECLARE
    z DOUBLE PRECISION := 1.96;
    p DOUBLE PRECISION;
    denom DOUBLE PRECISION;
    center DOUBLE PRECISION;
    factor DOUBLE PRECISION;
BEGIN
    IF n IS NULL OR n = 0 THEN
        ci_low := 0.0;
        ci_high := 0.0;
        RETURN;
    END IF;

    p := k::DOUBLE PRECISION / n::DOUBLE PRECISION;
    denom := 1.0 + (z * z) / n::DOUBLE PRECISION;
    center := p + (z * z) / (2.0 * n::DOUBLE PRECISION);
    factor := z * sqrt((p * (1.0 - p) + (z * z) / (4.0 * n::DOUBLE PRECISION)) / n::DOUBLE PRECISION);

    ci_low := GREATEST(0.0, (center - factor) / denom);
    ci_high := LEAST(1.0, (center + factor) / denom);
END $$;


-- ----------------------------------------------------------------------------
-- 13. METRICS AS VIEWS (A4)
-- ----------------------------------------------------------------------------

-- View 1: ASR by Surface
CREATE OR REPLACE VIEW ab.v_asr_by_surface AS
SELECT 
    surface,
    COUNT(*) FILTER (WHERE verdict = 'success') AS num,
    COUNT(*) AS den,
    (ab.wilson_ci(COUNT(*) FILTER (WHERE verdict = 'success')::INT, COUNT(*)::INT)).ci_low AS ci_low,
    (ab.wilson_ci(COUNT(*) FILTER (WHERE verdict = 'success')::INT, COUNT(*)::INT)).ci_high AS ci_high
FROM ab.attacks
GROUP BY surface;

-- View 2: Defense Block Rate
CREATE OR REPLACE VIEW ab.v_defense_block_rate AS
SELECT 
    defense_profile_version_id,
    COUNT(*) FILTER (WHERE verdict IN ('fixed', 'partially_mitigated')) AS num,
    COUNT(*) AS den,
    (ab.wilson_ci(COUNT(*) FILTER (WHERE verdict IN ('fixed', 'partially_mitigated'))::INT, COUNT(*)::INT)).ci_low AS ci_low,
    (ab.wilson_ci(COUNT(*) FILTER (WHERE verdict IN ('fixed', 'partially_mitigated'))::INT, COUNT(*)::INT)).ci_high AS ci_high
FROM ab.validation_results
GROUP BY defense_profile_version_id;

-- View 3: Adaptive Bypass Rate
CREATE OR REPLACE VIEW ab.v_adaptive_bypass_rate AS
SELECT 
    c.defense_profile_version_id,
    COUNT(*) FILTER (WHERE a.verdict = 'success') AS num,
    COUNT(*) AS den,
    (ab.wilson_ci(COUNT(*) FILTER (WHERE a.verdict = 'success')::INT, COUNT(*)::INT)).ci_low AS ci_low,
    (ab.wilson_ci(COUNT(*) FILTER (WHERE a.verdict = 'success')::INT, COUNT(*)::INT)).ci_high AS ci_high
FROM ab.attacks a
JOIN ab.campaigns c ON a.campaign_id = c.id
WHERE c.defense_profile_version_id IS NOT NULL
GROUP BY c.defense_profile_version_id;

-- View 4: Utility Retention
CREATE OR REPLACE VIEW ab.v_utility_retention AS
SELECT 
    campaign_id,
    AVG(utility_retention) AS mean_utility_retention,
    SUM(benign_pass) AS num,
    SUM(benign_total) AS den
FROM ab.eval_results
GROUP BY campaign_id;

-- View 5: Unauthorized Action Rate
CREATE OR REPLACE VIEW ab.v_unauthorized_action_rate AS
SELECT 
    r.target_version_id,
    COUNT(*) FILTER (WHERE e.payload->>'decision' = 'deny' OR e.payload->>'oracle_flag' = 'unauthorized_action') AS num,
    COUNT(*) FILTER (WHERE e.event_type = 'tool_proposed') AS den
FROM ab.events e
JOIN ab.runs r ON e.run_id = r.id
GROUP BY r.target_version_id;

-- View 6: Canary Leak Rate
CREATE OR REPLACE VIEW ab.v_leak_rate AS
SELECT 
    r.target_version_id,
    COUNT(*) FILTER (WHERE r.success = TRUE AND a.surface = 'instructions') AS num,
    COUNT(*) AS den
FROM ab.runs r
JOIN ab.attacks a ON r.attack_id = a.id
GROUP BY r.target_version_id;

-- View 7: Trace Completeness
CREATE OR REPLACE VIEW ab.v_trace_completeness AS
SELECT 
    run_id,
    COUNT(DISTINCT event_type) AS distinct_event_types,
    COUNT(*) AS total_events,
    MAX(seq) + 1 = COUNT(*) AS complete
FROM ab.events
GROUP BY run_id;

-- View 8: Replay Fidelity
CREATE OR REPLACE VIEW ab.v_replay_fidelity AS
SELECT 
    COUNT(*) FILTER (WHERE success = TRUE) AS num,
    COUNT(*) AS den
FROM ab.runs
WHERE kind = 'replay';

-- View 9: Mean Queries to First Break
CREATE OR REPLACE VIEW ab.v_mean_queries_to_first_break AS
SELECT 
    campaign_id,
    MIN(iteration) AS queries_to_first_break
FROM ab.attacks
WHERE verdict = 'success'
GROUP BY campaign_id;

-- View 10: Regression Delta
CREATE OR REPLACE VIEW ab.v_regression_delta AS
SELECT 
    defense_profile_version_id,
    summary->>'newly_vulnerable' AS newly_vulnerable_count,
    summary->>'newly_fixed' AS newly_fixed_count,
    summary->>'utility_drop' AS utility_drop_percent
FROM ab.regression_runs;

-- ----------------------------------------------------------------------------
-- 14. INDEXES
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_events_run_seq ON ab.events(run_id, seq);
CREATE INDEX IF NOT EXISTS idx_runs_attack_id ON ab.runs(attack_id);
CREATE INDEX IF NOT EXISTS idx_attacks_campaign_iter ON ab.attacks(campaign_id, iteration);
CREATE INDEX IF NOT EXISTS idx_findings_target_status ON ab.findings(target_version_id, status);
CREATE INDEX IF NOT EXISTS idx_model_calls_run_seq ON ab.model_calls(run_id, seq);
