-- ============================================================
--  APEX ARENA E-SPORTS EVENT — Supabase Schema
--  Run this SQL in your Supabase Dashboard → SQL Editor
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── TEAMS TABLE ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS teams (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    team_id         TEXT UNIQUE NOT NULL,     -- Human-readable ID e.g. BGMI-0001
    game            TEXT NOT NULL CHECK (game IN ('BGMI', 'Free Fire')),
    email           TEXT NOT NULL,
    branch          TEXT NOT NULL CHECK (branch IN ('CSE', 'AI&DS', 'ECE')),
    semester        TEXT NOT NULL,

    -- Captain (Player 1)
    captain_name    TEXT NOT NULL,
    captain_phone   TEXT NOT NULL,
    captain_usn     TEXT NOT NULL,

    -- Player 2
    player2_name    TEXT,
    player2_phone   TEXT,
    player2_usn     TEXT,

    -- Player 3
    player3_name    TEXT,
    player3_phone   TEXT,
    player3_usn     TEXT,

    -- Player 4
    player4_name    TEXT,
    player4_phone   TEXT,
    player4_usn     TEXT,

    -- Status
    payment_status  TEXT NOT NULL DEFAULT 'pending' CHECK (payment_status IN ('pending', 'paid', 'verified', 'rejected')),
    is_verified     BOOLEAN NOT NULL DEFAULT FALSE,

    -- Timestamps
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ─── AUTO-UPDATE updated_at ───────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_updated_at
    BEFORE UPDATE ON teams
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ─── SEQUENCE FOR HUMAN-READABLE TEAM IDs ────────────────────────────────────
CREATE SEQUENCE IF NOT EXISTS bgmi_team_seq START 1;
CREATE SEQUENCE IF NOT EXISTS freefire_team_seq START 1;

-- ─── INDEXES ─────────────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_teams_game           ON teams(game);
CREATE INDEX IF NOT EXISTS idx_teams_payment_status ON teams(payment_status);
CREATE INDEX IF NOT EXISTS idx_teams_captain_phone  ON teams(captain_phone);
CREATE INDEX IF NOT EXISTS idx_teams_email          ON teams(email);
CREATE INDEX IF NOT EXISTS idx_teams_created_at     ON teams(created_at);

-- ─── ROW LEVEL SECURITY (RLS) ─────────────────────────────────────────────────
-- Enable RLS but allow service_role full access (backend uses service_role key)
ALTER TABLE teams ENABLE ROW LEVEL SECURITY;

-- Public can INSERT (register)
CREATE POLICY "Allow public registration"
    ON teams FOR INSERT
    TO anon
    WITH CHECK (true);

-- Public can read count (for eventcount page)
CREATE POLICY "Allow public count read"
    ON teams FOR SELECT
    TO anon
    USING (true);

-- Service role has full access (backend admin operations)
CREATE POLICY "Service role full access"
    ON teams FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ─── ADMINS TABLE ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS admins (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username     TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE admins ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access admins"
    ON admins FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ─── SAMPLE DATA (optional — remove in production) ───────────────────────────
-- INSERT INTO teams (team_id, game, email, branch, semester, captain_name, captain_phone, captain_usn)
-- VALUES ('BGMI-0001', 'BGMI', 'test@example.com', 'CSE', '5', 'John Doe', '9876543210', '1XX21CS001');

-- ─── VERIFY AUTH TABLE (FOR VERIFY.HTML) ──────────────────────────────────────
CREATE TABLE IF NOT EXISTS verify_auth (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username     TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE verify_auth ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Service role full access verify_auth"
    ON verify_auth FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ─── INSERT DEFAULT CREDENTIALS ──────────────────────────────────────────────
-- Run these INSERTs in Supabase SQL Editor to seed the credentials.
-- The password_hash column stores the plain-text password (no hashing used).

-- Admin dashboard credentials (admin.html)
INSERT INTO admins (username, password_hash)
VALUES ('Esports', 'AI&DS')
ON CONFLICT (username) DO UPDATE SET password_hash = EXCLUDED.password_hash;

-- Verification page credentials (verify.html)
INSERT INTO verify_auth (username, password_hash)
VALUES ('Esports', 'AI&DS')
ON CONFLICT (username) DO UPDATE SET password_hash = EXCLUDED.password_hash;
