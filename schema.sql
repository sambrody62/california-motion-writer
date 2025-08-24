-- California Motion Writer Database Schema
-- PostgreSQL 15

-- Users table (authentication and basic info)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    email_verified BOOLEAN DEFAULT false
);

-- User profiles (reusable case information)
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    -- Case Information
    case_number VARCHAR(50),
    county VARCHAR(100) NOT NULL,
    court_branch VARCHAR(255),
    department VARCHAR(50),
    -- Party Information
    is_petitioner BOOLEAN NOT NULL,
    party_name VARCHAR(255) NOT NULL,
    party_address TEXT,
    party_phone VARCHAR(20),
    -- Other Party
    other_party_name VARCHAR(255) NOT NULL,
    other_party_address TEXT,
    other_party_attorney VARCHAR(255),
    -- Children
    children_info JSONB, -- Array of {name, dob, current_custody}
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

-- Motions table (each motion created)
CREATE TABLE motions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    profile_id UUID REFERENCES profiles(id),
    -- Motion Details
    motion_type VARCHAR(50) NOT NULL, -- 'RFO', 'RESPONSE', etc.
    status VARCHAR(50) NOT NULL DEFAULT 'draft', -- draft, completed, filed
    case_caption TEXT,
    -- Filing Info
    filing_date DATE,
    hearing_date DATE,
    hearing_time TIME,
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    -- Indexes
    INDEX idx_user_motions (user_id),
    INDEX idx_motion_status (status),
    INDEX idx_created_at (created_at DESC)
);

-- Motion drafts (Q&A responses and LLM outputs)
CREATE TABLE motion_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    motion_id UUID NOT NULL REFERENCES motions(id) ON DELETE CASCADE,
    -- Q&A Data
    step_number INTEGER NOT NULL,
    step_name VARCHAR(100), -- 'relief_requested', 'facts', 'best_interest', etc.
    question_data JSONB, -- Original questions and user answers
    -- LLM Processing
    llm_input TEXT, -- Combined context sent to LLM
    llm_output TEXT, -- Rewritten/enhanced text from LLM
    llm_model VARCHAR(50), -- Model version used
    llm_tokens_used INTEGER,
    -- Status
    is_complete BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Indexes
    UNIQUE(motion_id, step_number),
    INDEX idx_motion_drafts (motion_id)
);

-- Generated documents (PDFs)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    motion_id UUID NOT NULL REFERENCES motions(id) ON DELETE CASCADE,
    -- Document Info
    document_type VARCHAR(50) NOT NULL, -- 'FL-300', 'FL-320', etc.
    filename VARCHAR(255) NOT NULL,
    gcs_url TEXT NOT NULL,
    file_size_bytes INTEGER,
    pages INTEGER,
    -- Generation
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    generation_method VARCHAR(50), -- 'automated', 'manual_edit'
    -- Indexes
    INDEX idx_motion_documents (motion_id),
    INDEX idx_generated_at (generated_at DESC)
);

-- Audit log for compliance
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Indexes
    INDEX idx_audit_user (user_id),
    INDEX idx_audit_created (created_at DESC)
);

-- Create update triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER profiles_updated_at BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER motions_updated_at BEFORE UPDATE ON motions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER motion_drafts_updated_at BEFORE UPDATE ON motion_drafts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();