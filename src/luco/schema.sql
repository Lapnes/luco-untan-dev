-- Skema Database PostgreSQL untuk Luco: Single Active Session with Archiving

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    nim_or_nip VARCHAR(50),
    angkatan INT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL DEFAULT 'Percakapan Baru',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Aturan Integritas Database: Maksimal 1 sesi aktif per user
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_active_session_per_user ON chat_sessions(user_id) WHERE (is_active = true);
CREATE INDEX IF NOT EXISTS idx_sessions_user_time ON chat_sessions(user_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    citations JSONB DEFAULT '[]'::jsonb,
    clarification JSONB,
    feedback VARCHAR(10),
    feedback_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Indeks JSONB untuk pelacakan sitasi transparan
CREATE INDEX IF NOT EXISTS idx_messages_citations ON chat_messages USING gin(citations);

-- Indeks Sesi & User untuk pengurutan cepat
CREATE INDEX IF NOT EXISTS idx_messages_session_time ON chat_messages(session_id, created_at ASC);
CREATE INDEX IF NOT EXISTS idx_messages_user_time ON chat_messages(user_id, created_at DESC);

-- Tabel Audit & Monitoring untuk Penelitian & Estimasi Biaya
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    user_email VARCHAR(255),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
    message_id UUID REFERENCES chat_messages(id) ON DELETE SET NULL,
    endpoint VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    prompt_tokens INT DEFAULT 0,
    completion_tokens INT DEFAULT 0,
    total_tokens INT DEFAULT 0,
    estimated_cost_usd NUMERIC(10, 6) DEFAULT 0,
    latency_s NUMERIC(6, 2) DEFAULT 0,
    steps INT DEFAULT 0,
    tool_calls JSONB DEFAULT '[]'::jsonb,
    system_prompt TEXT,
    user_prompt TEXT,
    user_prompt_tokens INT DEFAULT 0,
    system_prompt_tokens INT DEFAULT 0,
    context_tokens INT DEFAULT 0,
    timing_breakdown JSONB DEFAULT '{}'::jsonb,
    feedback VARCHAR(10),
    rejected BOOLEAN DEFAULT FALSE,
    reason VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_time ON audit_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_model ON audit_logs(model);
