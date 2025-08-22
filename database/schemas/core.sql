-- VectorBid Core Database Schema
-- Comprehensive schema for pilot contract management and authentication

-- ============================================================================
-- EXTENSIONS AND FUNCTIONS
-- ============================================================================

-- UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Encryption support
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Audit timestamp function
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- USER AUTHENTICATION AND MANAGEMENT
-- ============================================================================

-- User accounts (pilots, admins, etc.)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- bcrypt hash
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'pilot', -- pilot, admin, approver
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, suspended, deleted
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires_at TIMESTAMP WITH TIME ZONE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User sessions for JWT management
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL, -- SHA-256 hash of JWT
    device_info JSONB, -- User agent, IP, etc.
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    revoked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Pilot profiles (extends users table)
CREATE TABLE pilots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    pilot_id VARCHAR(50) UNIQUE NOT NULL, -- Airline employee ID
    airline VARCHAR(10) NOT NULL, -- UAL, DAL, AAL, SWA, etc.
    base VARCHAR(10) NOT NULL, -- ORD, DEN, SFO, etc.
    seat VARCHAR(10) NOT NULL, -- CA, FO
    equipment JSONB NOT NULL DEFAULT '[]', -- ["737", "787", "777"]
    hire_date DATE,
    seniority_number INTEGER,
    seniority_percentile DECIMAL(5,4), -- 0.0000 to 1.0000
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, retired, furloughed
    metadata JSONB DEFAULT '{}', -- Additional pilot-specific data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AIRLINE AND REGULATORY DATA
-- ============================================================================

-- Airlines master table
CREATE TABLE airlines (
    code VARCHAR(10) PRIMARY KEY, -- UAL, DAL, AAL, SWA
    name VARCHAR(255) NOT NULL, -- United Airlines
    country VARCHAR(10) NOT NULL DEFAULT 'US',
    active BOOLEAN DEFAULT TRUE,
    pbs_system VARCHAR(100), -- Jeppesen, AIMS, etc.
    timezone VARCHAR(50) DEFAULT 'UTC',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- FAR 117 and regulatory rules (comprehensive)
CREATE TABLE regulatory_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id VARCHAR(50) UNIQUE NOT NULL, -- FAR117_DUTY_LIMIT_14H
    category VARCHAR(50) NOT NULL, -- far117, far121, etc.
    section VARCHAR(100), -- 117.13(a)(1)
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    rule_text TEXT NOT NULL, -- Full regulatory text
    citation VARCHAR(200), -- FAR 117.13(a)(1)
    authority VARCHAR(100), -- FAA, DOT, etc.
    effective_date DATE NOT NULL,
    expiration_date DATE, -- NULL for permanent rules
    is_hard_constraint BOOLEAN DEFAULT TRUE,
    weight DECIMAL(3,2) DEFAULT 1.00, -- 0.00 to 1.00
    applies_to JSONB DEFAULT '{}', -- {"airlines": ["ALL"], "aircraft": [], "routes": []}
    parameters JSONB DEFAULT '{}', -- Rule-specific parameters
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CONTRACT MANAGEMENT
-- ============================================================================

-- Contract templates (uploaded by pilots, approved by community)
CREATE TABLE pilot_contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    airline VARCHAR(10) NOT NULL REFERENCES airlines(code),
    contract_version VARCHAR(100) NOT NULL, -- CBA-2024, LOA-2025-01
    contract_type VARCHAR(50) NOT NULL, -- cba, loa, company_policy, custom
    title VARCHAR(500) NOT NULL,
    description TEXT,
    uploaded_by UUID NOT NULL REFERENCES users(id),
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    approved_by UUID REFERENCES users(id), -- Null until approved
    approved_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, approved, active, deprecated
    effective_date DATE,
    expiration_date DATE,
    source_document TEXT, -- Original contract text
    parsing_method VARCHAR(50) NOT NULL, -- llm, manual, hybrid
    parsing_confidence DECIMAL(3,2), -- 0.00 to 1.00
    community_rating DECIMAL(3,2), -- 0.00 to 5.00
    usage_count INTEGER DEFAULT 0, -- How many pilots use this contract
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique contract versions per airline
    UNIQUE(airline, contract_version)
);

-- Individual contract rules (parsed from contracts)
CREATE TABLE contract_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_id UUID NOT NULL REFERENCES pilot_contracts(id) ON DELETE CASCADE,
    rule_id VARCHAR(100) NOT NULL, -- MAX_DUTY_HOURS_DOMESTIC
    category VARCHAR(50) NOT NULL, -- far117, union, company, custom
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    rule_text TEXT NOT NULL, -- Exact wording from contract
    citation VARCHAR(200), -- Contract section reference
    is_hard_constraint BOOLEAN DEFAULT TRUE,
    weight DECIMAL(3,2) DEFAULT 1.00, -- 0.00 to 1.00
    applies_to JSONB DEFAULT '{}', -- Conditions when rule applies
    parameters JSONB DEFAULT '{}', -- Rule-specific parameters
    effective_date DATE,
    expiration_date DATE,
    parsing_confidence DECIMAL(3,2), -- How confident we are in this parsing
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Ensure unique rule IDs within each contract
    UNIQUE(contract_id, rule_id)
);

-- Pilot contract assignments (which contract each pilot uses)
CREATE TABLE pilot_contract_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pilot_id UUID NOT NULL REFERENCES pilots(id) ON DELETE CASCADE,
    contract_id UUID NOT NULL REFERENCES pilot_contracts(id),
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by UUID NOT NULL REFERENCES users(id), -- Self-assigned or admin
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- active, inactive
    notes TEXT, -- Why this assignment was made
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- One active contract per pilot
    UNIQUE(pilot_id) WHERE status = 'active'
);

-- ============================================================================
-- COMMUNITY AND FEEDBACK
-- ============================================================================

-- Contract ratings and reviews from pilots
CREATE TABLE contract_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_id UUID NOT NULL REFERENCES pilot_contracts(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES users(id),
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    accuracy_rating INTEGER CHECK (accuracy_rating >= 1 AND accuracy_rating <= 5),
    completeness_rating INTEGER CHECK (completeness_rating >= 1 AND completeness_rating <= 5),
    review_text TEXT,
    helpful_votes INTEGER DEFAULT 0,
    flagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- One review per pilot per contract
    UNIQUE(contract_id, reviewer_id)
);

-- Community contributions and improvements
CREATE TABLE contract_improvements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_id UUID NOT NULL REFERENCES pilot_contracts(id) ON DELETE CASCADE,
    contributor_id UUID NOT NULL REFERENCES users(id),
    improvement_type VARCHAR(50) NOT NULL, -- rule_addition, rule_correction, metadata
    description TEXT NOT NULL,
    proposed_changes JSONB NOT NULL, -- Structured change proposal
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, approved, rejected
    reviewed_by UUID REFERENCES users(id),
    reviewed_at TIMESTAMP WITH TIME ZONE,
    review_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- AUDIT AND SECURITY
-- ============================================================================

-- Comprehensive audit log
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id), -- NULL for system actions
    action VARCHAR(100) NOT NULL, -- login, contract_upload, rule_update, etc.
    entity_type VARCHAR(50) NOT NULL, -- user, contract, rule, etc.
    entity_id UUID, -- ID of affected entity
    old_values JSONB, -- Previous state
    new_values JSONB, -- New state
    ip_address INET,
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    error_message TEXT, -- If success = false
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Security events and monitoring
CREATE TABLE security_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL, -- failed_login, suspicious_activity, etc.
    severity VARCHAR(20) NOT NULL, -- low, medium, high, critical
    user_id UUID REFERENCES users(id),
    ip_address INET,
    user_agent TEXT,
    details JSONB NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_by UUID REFERENCES users(id),
    resolved_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PERFORMANCE INDEXES
-- ============================================================================

-- User and authentication indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role_status ON users(role, status);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_user_sessions_token_hash ON user_sessions(token_hash);

-- Pilot indexes
CREATE INDEX idx_pilots_user_id ON pilots(user_id);
CREATE INDEX idx_pilots_pilot_id ON pilots(pilot_id);
CREATE INDEX idx_pilots_airline ON pilots(airline);
CREATE INDEX idx_pilots_base ON pilots(base);
CREATE INDEX idx_pilots_status ON pilots(status);

-- Contract and rule indexes
CREATE INDEX idx_pilot_contracts_airline ON pilot_contracts(airline);
CREATE INDEX idx_pilot_contracts_status ON pilot_contracts(status);
CREATE INDEX idx_pilot_contracts_uploaded_by ON pilot_contracts(uploaded_by);
CREATE INDEX idx_contract_rules_contract_id ON contract_rules(contract_id);
CREATE INDEX idx_contract_rules_category ON contract_rules(category);
CREATE INDEX idx_contract_rules_rule_id ON contract_rules(rule_id);

-- Assignment and review indexes
CREATE INDEX idx_pilot_contract_assignments_pilot_id ON pilot_contract_assignments(pilot_id);
CREATE INDEX idx_pilot_contract_assignments_status ON pilot_contract_assignments(status);
CREATE INDEX idx_contract_reviews_contract_id ON contract_reviews(contract_id);
CREATE INDEX idx_contract_reviews_reviewer_id ON contract_reviews(reviewer_id);

-- Regulatory rule indexes
CREATE INDEX idx_regulatory_rules_category ON regulatory_rules(category);
CREATE INDEX idx_regulatory_rules_rule_id ON regulatory_rules(rule_id);
CREATE INDEX idx_regulatory_rules_effective_date ON regulatory_rules(effective_date);

-- Audit indexes
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_entity_type ON audit_log(entity_type);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_security_events_event_type ON security_events(event_type);
CREATE INDEX idx_security_events_user_id ON security_events(user_id);
CREATE INDEX idx_security_events_created_at ON security_events(created_at);

-- ============================================================================
-- TRIGGERS FOR AUDIT TRAILS
-- ============================================================================

-- Update timestamps
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_pilots_updated_at BEFORE UPDATE ON pilots
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_airlines_updated_at BEFORE UPDATE ON airlines
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_regulatory_rules_updated_at BEFORE UPDATE ON regulatory_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_pilot_contracts_updated_at BEFORE UPDATE ON pilot_contracts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_contract_rules_updated_at BEFORE UPDATE ON contract_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_contract_reviews_updated_at BEFORE UPDATE ON contract_reviews
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================================
-- VIEWS FOR COMMON QUERIES
-- ============================================================================

-- Complete pilot profile with contract information
CREATE VIEW pilot_profiles AS
SELECT 
    p.id,
    p.pilot_id,
    u.first_name,
    u.last_name,
    u.email,
    p.airline,
    p.base,
    p.seat,
    p.equipment,
    p.seniority_number,
    p.seniority_percentile,
    pc.id as contract_id,
    pc.contract_version,
    pc.title as contract_title,
    pca.assigned_at as contract_assigned_at,
    COUNT(cr.id) as contract_rule_count
FROM pilots p
JOIN users u ON p.user_id = u.id
LEFT JOIN pilot_contract_assignments pca ON p.id = pca.pilot_id AND pca.status = 'active'
LEFT JOIN pilot_contracts pc ON pca.contract_id = pc.id
LEFT JOIN contract_rules cr ON pc.id = cr.contract_id
WHERE u.status = 'active' AND p.status = 'active'
GROUP BY p.id, u.first_name, u.last_name, u.email, p.airline, p.base, p.seat, 
         p.equipment, p.seniority_number, p.seniority_percentile, pc.id, 
         pc.contract_version, pc.title, pca.assigned_at;

-- Active contracts with statistics
CREATE VIEW contract_statistics AS
SELECT 
    pc.id,
    pc.airline,
    pc.contract_version,
    pc.title,
    pc.status,
    COUNT(DISTINCT cr.id) as rule_count,
    COUNT(DISTINCT pca.pilot_id) as pilot_count,
    AVG(rev.rating) as average_rating,
    COUNT(DISTINCT rev.id) as review_count,
    pc.created_at,
    pc.approved_at
FROM pilot_contracts pc
LEFT JOIN contract_rules cr ON pc.id = cr.contract_id
LEFT JOIN pilot_contract_assignments pca ON pc.id = pca.contract_id AND pca.status = 'active'
LEFT JOIN contract_reviews rev ON pc.id = rev.contract_id
GROUP BY pc.id, pc.airline, pc.contract_version, pc.title, pc.status, pc.created_at, pc.approved_at;

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) SETUP
-- ============================================================================

-- Enable RLS on sensitive tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE pilots ENABLE ROW LEVEL SECURITY;
ALTER TABLE pilot_contract_assignments ENABLE ROW LEVEL SECURITY;
ALTER TABLE contract_reviews ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- RLS Policies will be added in separate security configuration file