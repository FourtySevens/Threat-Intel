-- Idempotent schema and additive migration for Threat Intel.
-- Run with: python -m scraper.jobs init-db

-- CVE table for storing CVE information
CREATE TABLE IF NOT EXISTS cve (
    id BIGSERIAL PRIMARY KEY,
    cve_id VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    cvss_score DECIMAL(3,1),
    severity VARCHAR(20),
    source VARCHAR(50),
    source_identifier VARCHAR(255),
    published_at TIMESTAMPTZ,
    last_modified_at TIMESTAMPTZ,
    attack_vector VARCHAR(32),
    cvss_vector TEXT,
    exploitability_score NUMERIC(5,2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Upgrades installations made with the original schema.
ALTER TABLE cve ADD COLUMN IF NOT EXISTS source_identifier VARCHAR(255);
ALTER TABLE cve ADD COLUMN IF NOT EXISTS published_at TIMESTAMPTZ;
ALTER TABLE cve ADD COLUMN IF NOT EXISTS last_modified_at TIMESTAMPTZ;
ALTER TABLE cve ADD COLUMN IF NOT EXISTS attack_vector VARCHAR(32);
ALTER TABLE cve ADD COLUMN IF NOT EXISTS cvss_vector TEXT;
ALTER TABLE cve ADD COLUMN IF NOT EXISTS exploitability_score NUMERIC(5,2);

-- KEV (Known Exploited Vulnerabilities) table
CREATE TABLE IF NOT EXISTS cve_kev (
    id BIGSERIAL PRIMARY KEY,
    cve_id BIGINT NOT NULL REFERENCES cve(id) ON DELETE CASCADE,
    exploited BOOLEAN NOT NULL DEFAULT TRUE,
    date_added DATE,
    due_date DATE,
    required_action TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cve_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_cve_cve_id ON cve(cve_id);
CREATE INDEX IF NOT EXISTS idx_cve_kev_cve_id ON cve_kev(cve_id);
CREATE INDEX IF NOT EXISTS idx_cve_last_modified_at ON cve(last_modified_at);

CREATE TABLE IF NOT EXISTS rss_feeds (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    feed_url TEXT NOT NULL UNIQUE,
    source_type VARCHAR(32) NOT NULL DEFAULT 'research',
    reliability VARCHAR(16) NOT NULL DEFAULT 'medium',
    default_priority SMALLINT NOT NULL DEFAULT 3,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    last_fetched_at TIMESTAMPTZ,
    last_success_at TIMESTAMPTZ,
    last_failure_at TIMESTAMPTZ,
    failure_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE rss_feeds ADD COLUMN IF NOT EXISTS source_type VARCHAR(32) NOT NULL DEFAULT 'research';
ALTER TABLE rss_feeds ADD COLUMN IF NOT EXISTS reliability VARCHAR(16) NOT NULL DEFAULT 'medium';
ALTER TABLE rss_feeds ADD COLUMN IF NOT EXISTS default_priority SMALLINT NOT NULL DEFAULT 3;
ALTER TABLE rss_feeds ADD COLUMN IF NOT EXISTS last_success_at TIMESTAMPTZ;
ALTER TABLE rss_feeds ADD COLUMN IF NOT EXISTS last_failure_at TIMESTAMPTZ;
ALTER TABLE rss_feeds ADD COLUMN IF NOT EXISTS failure_count INTEGER NOT NULL DEFAULT 0;

CREATE TABLE IF NOT EXISTS articles (
    id BIGSERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    source VARCHAR(100) NOT NULL,
    published_at TIMESTAMPTZ,
    content TEXT NOT NULL,
    content_hash CHAR(64) NOT NULL UNIQUE,
    canonical_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE articles ADD COLUMN IF NOT EXISTS rss_feed_id BIGINT REFERENCES rss_feeds(id) ON DELETE SET NULL;
ALTER TABLE articles ADD COLUMN IF NOT EXISTS canonical_url TEXT;
UPDATE articles SET canonical_url = url WHERE canonical_url IS NULL;

CREATE TABLE IF NOT EXISTS tags (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS article_tags (
    article_id BIGINT NOT NULL REFERENCES articles(id) ON DELETE CASCADE,
    tag_id BIGINT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (article_id, tag_id)
);

CREATE TABLE IF NOT EXISTS job_state (
    job_name VARCHAR(100) PRIMARY KEY,
    last_successful_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_articles_source_published_at ON articles(source, published_at DESC);
CREATE INDEX IF NOT EXISTS idx_articles_rss_feed_id ON articles(rss_feed_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_canonical_url ON articles(canonical_url) WHERE canonical_url IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_rss_feeds_health ON rss_feeds(enabled, failure_count DESC, last_success_at);
