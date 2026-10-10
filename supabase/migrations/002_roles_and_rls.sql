-- ============================================================================
-- AGENTBREAK: Supabase Database Migration 002 - Roles, RLS & Access Control
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. ROLE CREATION & PRIVILEGES
-- ----------------------------------------------------------------------------
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'ab_app') THEN
        CREATE ROLE ab_app LOGIN;
    END IF;
END $$;

GRANT USAGE ON SCHEMA ab TO ab_app;

-- Grant SELECT, INSERT, UPDATE on mutable tables
GRANT SELECT, INSERT, UPDATE ON ab.profiles TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.targets TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.target_versions TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.rag_sources TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.fixtures TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.canaries TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.defense_profiles TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.defense_profile_versions TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.campaigns TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.attacks TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.runs TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.findings TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.finding_evidence TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.attack_corpus TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.audit_findings TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.benign_tasks TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.validation_results TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.eval_results TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.regression_runs TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.approvals TO ab_app;
GRANT SELECT, INSERT, UPDATE ON ab.reports TO ab_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ab.llm_cache TO ab_app;

-- Grant SELECT, INSERT ONLY on append-only tables (No UPDATE or DELETE)
GRANT SELECT, INSERT ON ab.events TO ab_app;
GRANT SELECT, INSERT ON ab.run_seals TO ab_app;
GRANT SELECT, INSERT ON ab.model_calls TO ab_app;
GRANT SELECT, INSERT ON ab.audit_log TO ab_app;

-- Grant SELECT on views & lookup tables
GRANT SELECT ON ALL TABLES IN SCHEMA ab TO ab_app;

-- ----------------------------------------------------------------------------
-- 2. ROW LEVEL SECURITY (RLS) - DEFAULT DENY FOR PUBLIC / ANON / AUTHENTICATED
-- ----------------------------------------------------------------------------
ALTER TABLE ab.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.profiles FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.targets ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.targets FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.target_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.target_versions FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.rag_sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.rag_sources FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.fixtures ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.fixtures FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.canaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.canaries FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.defense_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.defense_profiles FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.defense_profile_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.defense_profile_versions FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.campaigns FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.attacks ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.attacks FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.runs FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.events ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.events FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.run_seals ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.run_seals FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.model_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.model_calls FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.llm_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.llm_cache FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.findings FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.finding_evidence ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.finding_evidence FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.attack_corpus ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.attack_corpus FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.audit_findings ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.audit_findings FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.benign_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.benign_tasks FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.validation_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.validation_results FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.eval_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.eval_results FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.regression_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.regression_runs FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.approvals ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.approvals FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.reports FORCE ROW LEVEL SECURITY;

ALTER TABLE ab.audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE ab.audit_log FORCE ROW LEVEL SECURITY;

-- ----------------------------------------------------------------------------
-- 3. RLS POLICIES (Backend Role Bypass / User Role Policies)
-- ----------------------------------------------------------------------------

-- Helper function to read user's role from JWT app_metadata
CREATE OR REPLACE FUNCTION ab.app_role() RETURNS TEXT LANGUAGE sql STABLE AS $$
    SELECT COALESCE(
        current_setting('request.jwt.claims', true)::jsonb -> 'app_metadata' ->> 'role',
        'viewer'
    );
$$;

-- Backend Role Policy (Full Access for ab_app)
CREATE POLICY p_ab_app_all ON ab.profiles FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_targets ON ab.targets FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_target_versions ON ab.target_versions FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_rag_sources ON ab.rag_sources FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_fixtures ON ab.fixtures FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_canaries ON ab.canaries FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_defense_profiles ON ab.defense_profiles FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_defense_profile_versions ON ab.defense_profile_versions FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_campaigns ON ab.campaigns FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_attacks ON ab.attacks FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_runs ON ab.runs FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_events ON ab.events FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_run_seals ON ab.run_seals FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_model_calls ON ab.model_calls FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_llm_cache ON ab.llm_cache FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_findings ON ab.findings FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_finding_evidence ON ab.finding_evidence FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_attack_corpus ON ab.attack_corpus FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_audit_findings ON ab.audit_findings FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_benign_tasks ON ab.benign_tasks FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_validation_results ON ab.validation_results FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_eval_results ON ab.eval_results FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_regression_runs ON ab.regression_runs FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_approvals ON ab.approvals FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_reports ON ab.reports FOR ALL TO ab_app USING (true) WITH CHECK (true);
CREATE POLICY p_ab_app_audit_log ON ab.audit_log FOR ALL TO ab_app USING (true) WITH CHECK (true);
