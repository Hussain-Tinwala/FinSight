-- Create the standard relational table
CREATE TABLE cloud_spend (
    timestamp TIMESTAMPTZ NOT NULL,
    cloud_provider VARCHAR(50) NOT NULL,
    unified_category VARCHAR(50) NOT NULL,
    cost DOUBLE PRECISION NOT NULL,
    normalized_env VARCHAR(50),
    normalized_team VARCHAR(50),
    is_anomaly INTEGER DEFAULT 0,
    anomaly_type VARCHAR(50) DEFAULT 'none'
);

-- Convert it into a TimescaleDB Hypertable partitioned by time
-- We will use 7-day chunks as default for daily/hourly billing data
SELECT create_hypertable('cloud_spend', 'timestamp', chunk_time_interval => INTERVAL '7 days');

-- Create indexes for faster querying by our APIs
CREATE INDEX ix_cloud_provider ON cloud_spend (cloud_provider, timestamp DESC);
CREATE INDEX ix_unified_category ON cloud_spend (unified_category, timestamp DESC);
CREATE INDEX ix_team ON cloud_spend (normalized_team, timestamp DESC);