-- Migration 001: Initial VectorBid Database Schema
-- Creates all core tables, indexes, and constraints

-- ============================================================================
-- MIGRATION METADATA
-- ============================================================================

-- Track migration
INSERT INTO schema_migrations (version, description, applied_at) 
VALUES ('001', 'Initial VectorBid database schema', NOW());

-- ============================================================================
-- EXECUTE CORE SCHEMA
-- ============================================================================

-- Load the main schema file
\i '../schemas/core.sql';

-- ============================================================================
-- SEED DEFAULT DATA
-- ============================================================================

-- Insert default airlines
INSERT INTO airlines (code, name, country, pbs_system, timezone) VALUES
('UAL', 'United Airlines', 'US', 'Jeppesen', 'America/Chicago'),
('DAL', 'Delta Air Lines', 'US', 'AIMS', 'America/New_York'),
('AAL', 'American Airlines', 'US', 'AIMS', 'America/Chicago'),
('SWA', 'Southwest Airlines', 'US', 'Sabre', 'America/Chicago'),
('JBU', 'JetBlue Airways', 'US', 'Sabre', 'America/New_York'),
('ASA', 'Alaska Airlines', 'US', 'Sabre', 'America/Los_Angeles');

-- Create default admin user (password: 'admin123' - CHANGE IN PRODUCTION!)
INSERT INTO users (id, email, password_hash, first_name, last_name, role, status, email_verified)
VALUES (
    uuid_generate_v4(),
    'admin@vectorbid.com',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj5Ns0xJVHqG', -- bcrypt hash of 'admin123'
    'System',
    'Administrator',
    'admin',
    'active',
    true
);

-- Load FAR 117 rules
\i '../seeds/far117_rules.sql';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify table creation
DO $$
DECLARE
    table_count INTEGER;
    rule_count INTEGER;
    airline_count INTEGER;
BEGIN
    -- Count tables
    SELECT COUNT(*) INTO table_count 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_type = 'BASE TABLE';
    
    -- Count FAR 117 rules
    SELECT COUNT(*) INTO rule_count 
    FROM regulatory_rules 
    WHERE category = 'far117';
    
    -- Count airlines
    SELECT COUNT(*) INTO airline_count 
    FROM airlines;
    
    RAISE NOTICE 'Migration 001 completed successfully:';
    RAISE NOTICE '- Created % database tables', table_count;
    RAISE NOTICE '- Loaded % FAR 117 rules', rule_count;
    RAISE NOTICE '- Seeded % airlines', airline_count;
    RAISE NOTICE '- Created system administrator account';
END $$;

-- ============================================================================
-- PERMISSIONS AND SECURITY
-- ============================================================================

-- Create database roles
CREATE ROLE vectorbid_app;
CREATE ROLE vectorbid_readonly;
CREATE ROLE vectorbid_admin;

-- Grant permissions
GRANT CONNECT ON DATABASE vectorbid TO vectorbid_app;
GRANT USAGE ON SCHEMA public TO vectorbid_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO vectorbid_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO vectorbid_app;

-- Read-only access
GRANT CONNECT ON DATABASE vectorbid TO vectorbid_readonly;
GRANT USAGE ON SCHEMA public TO vectorbid_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO vectorbid_readonly;

-- Admin access
GRANT ALL PRIVILEGES ON DATABASE vectorbid TO vectorbid_admin;

COMMIT;