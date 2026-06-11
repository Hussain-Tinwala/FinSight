-- Activate standard UUID generation extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- CLEAN SLATE RESET: Drops old tables to clear schema conflicts
DROP TABLE IF EXISTS cloud_forecast CASCADE;
DROP TABLE IF EXISTS cloud_spend CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;

-- 1. ORGANIZATIONS TABLE (SaaS Tenants)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    tier VARCHAR(50) DEFAULT 'FREE', -- FREE, ENTERPRISE, PREMIUM
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. USERS TABLE (Corporate Accounts linked to Tenants)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(50) DEFAULT 'VIEWER', -- ADMIN, ENGINEER, VIEWER
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 3. UPGRADED MULTI-TENANT CLOUD SPEND TABLE
CREATE TABLE cloud_spend (
    id BIGSERIAL,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    timestamp TIMESTAMPTZ NOT NULL,
    cloud_provider VARCHAR(50) NOT NULL,    -- AWS, GCP, Azure
    unified_category VARCHAR(50) NOT NULL,  -- COMPUTE, STORAGE, NETWORK
    cost DOUBLE PRECISION NOT NULL,
    normalized_env VARCHAR(50) DEFAULT 'unknown',
    normalized_team VARCHAR(50) DEFAULT 'unknown',
    is_anomaly INT DEFAULT 0,
    anomaly_type VARCHAR(50) DEFAULT 'none',
    PRIMARY KEY (id, organization_id, timestamp)
);

-- 4. UPGRADED MULTI-TENANT FORECAST PLANNED CURVES TABLE
CREATE TABLE cloud_forecast (
    id BIGSERIAL,
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    cloud_provider VARCHAR(50) NOT NULL,
    unified_category VARCHAR(50) NOT NULL,
    predicted_cost DOUBLE PRECISION NOT NULL,
    lower_bound DOUBLE PRECISION NOT NULL,
    upper_bound DOUBLE PRECISION NOT NULL,
    model_used VARCHAR(50) NOT NULL,
    PRIMARY KEY (id, organization_id, date)
);

-- --- High-Performance Multi-Tenant Composite Indexes ---
CREATE INDEX ix_spend_tenant_lookup 
ON cloud_spend (organization_id, cloud_provider, timestamp DESC);

CREATE INDEX ix_spend_anomaly_feed 
ON cloud_spend (organization_id, is_anomaly) 
WHERE is_anomaly = 1;

CREATE INDEX ix_forecast_tenant_lookup 
ON cloud_forecast (organization_id, date ASC);

-- Insert global mock organizations to seed the environment
INSERT INTO organizations (id, name, tier) VALUES 
('a0000000-0000-0000-0000-000000000001', 'FinTech Global Corp', 'ENTERPRISE'),
('b0000000-0000-0000-0000-000000000002', 'Alpha Software Analytics', 'FREE');