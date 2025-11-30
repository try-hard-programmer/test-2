-- ================================================================
-- SUPABASE MIGRATION V3 - TELEGRAM DASHBOARD (FULL VERSION)
-- ================================================================
-- Purpose: Complete ticket system with audit trail & performance
-- Safe to run multiple times (uses IF NOT EXISTS)
-- Run this in: Supabase SQL Editor
-- ================================================================

-- ================================================================
-- PART 1: TELEGRAM ACCOUNTS TABLE
-- ================================================================

CREATE TABLE IF NOT EXISTS telegram_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_label TEXT NOT NULL,
    persona TEXT,
    knowledge TEXT,
    schedule JSONB,
    integration JSONB,
    ticketing_settings JSONB,
    api_id INTEGER NOT NULL,
    api_hash TEXT NOT NULL,
    session_string TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Asia/Jakarta')
);

-- Example data structure:
-- persona: "Friendly customer support agent"
-- knowledge: "Product catalog, FAQ, policies"
-- schedule: {"timezone": "Asia/Jakarta", "work_hours": "09:00-17:00", "days": ["Mon","Tue","Wed","Thu","Fri"]}
-- integration: {"whatsapp": false, "email": false, "telegram": true}
-- ticketing_settings: {"auto_assign": true, "max_tickets": 10, "priority_rules": "auto"}

-- Performance: Index for filtering active accounts
CREATE INDEX IF NOT EXISTS idx_telegram_accounts_is_active 
ON telegram_accounts(is_active);

-- Security: Enable Row Level Security
ALTER TABLE telegram_accounts ENABLE ROW LEVEL SECURITY;

-- Security: Allow service role full access
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'telegram_accounts' 
        AND policyname = 'Enable all access for service role'
    ) THEN
        CREATE POLICY "Enable all access for service role" 
        ON telegram_accounts 
        FOR ALL 
        USING (true);
    END IF;
END $$;

-- Permissions
GRANT ALL ON telegram_accounts TO service_role;
GRANT ALL ON telegram_accounts TO anon;

-- ================================================================
-- PART 2: TICKETS TABLE (Enhanced with Tracking)
-- ================================================================

CREATE TABLE IF NOT EXISTS tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id UUID NOT NULL REFERENCES telegram_accounts(id) ON DELETE CASCADE,
    chat_id TEXT NOT NULL,
    
    -- Core Fields
    status TEXT DEFAULT 'open',
    priority TEXT DEFAULT 'medium',
    source TEXT DEFAULT 'manual',
    subject TEXT,
    description TEXT,
    
    -- Timestamps (NEW: updated_at for tracking changes)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Asia/Jakarta'),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Asia/Jakarta'),
    
    -- Validation Constraints
    CONSTRAINT valid_status CHECK (status IN ('open', 'in_progress', 'resolved', 'closed')),
    CONSTRAINT valid_priority CHECK (priority IN ('low', 'medium', 'high', 'urgent')),
    CONSTRAINT valid_source CHECK (source IN ('auto', 'manual', 'user_command', 'ai'))
);

-- ================================================================
-- PART 3: TICKET HISTORY TABLE (AUDIT TRAIL)
-- ================================================================

CREATE TABLE IF NOT EXISTS ticket_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id UUID NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    changed_by TEXT NOT NULL,  -- agent name, "system", "customer"
    field_changed TEXT NOT NULL,  -- "status", "priority", "assigned_to", etc
    old_value TEXT,
    new_value TEXT NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Asia/Jakarta')
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ticket_history_ticket_id ON ticket_history(ticket_id);
CREATE INDEX IF NOT EXISTS idx_ticket_history_changed_at ON ticket_history(changed_at DESC);

-- Security: Enable Row Level Security
ALTER TABLE ticket_history ENABLE ROW LEVEL SECURITY;

-- Security: Allow service role full access
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'ticket_history' 
        AND policyname = 'Enable all access for service role'
    ) THEN
        CREATE POLICY "Enable all access for service role" 
        ON ticket_history 
        FOR ALL 
        USING (true);
    END IF;
END $$;

-- Permissions
GRANT ALL ON ticket_history TO service_role;
GRANT ALL ON ticket_history TO anon;

-- Add comment
COMMENT ON TABLE ticket_history IS 'Audit trail for all ticket changes - tracks who changed what and when';

-- ================================================================
-- PART 4: ADD COLUMNS TO EXISTING TABLES (Safe if already exists)
-- ================================================================

-- Add updated_at if it doesn't exist (for existing deployments)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'tickets' AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE tickets 
        ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() AT TIME ZONE 'Asia/Jakarta');
    END IF;
END $$;

-- ================================================================
-- PART 5: PERFORMANCE INDEXES
-- ================================================================

-- Index 1: Active tickets lookup (for checking if chat has open ticket)
CREATE INDEX IF NOT EXISTS idx_tickets_active 
ON tickets(account_id, chat_id) 
WHERE status IN ('open', 'in_progress');

-- Index 2: Date filtering (for MTD summary and reports)
CREATE INDEX IF NOT EXISTS idx_tickets_created_at 
ON tickets(created_at DESC);

-- Index 3: Compound index for filtered queries (status + date)
CREATE INDEX IF NOT EXISTS idx_tickets_status_created 
ON tickets(status, created_at DESC);

-- Index 4: Updated_at for "recent activity" queries
CREATE INDEX IF NOT EXISTS idx_tickets_updated_at 
ON tickets(updated_at DESC);

-- Index 5: Priority filtering (for high-priority ticket queries)
CREATE INDEX IF NOT EXISTS idx_tickets_priority 
ON tickets(priority);

-- ================================================================
-- PART 6: AUTO-UPDATE TRIGGER (updated_at timestamp)
-- ================================================================

-- Function: Auto-update updated_at on any ticket change
CREATE OR REPLACE FUNCTION update_ticket_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW() AT TIME ZONE 'Asia/Jakarta';
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists (to avoid duplicate trigger error)
DROP TRIGGER IF EXISTS update_ticket_modtime ON tickets;

-- Create trigger
CREATE TRIGGER update_ticket_modtime
    BEFORE UPDATE ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION update_ticket_timestamp();

-- ================================================================
-- PART 7: AUTO-LOG TICKET CHANGES TRIGGER (AUDIT TRAIL)
-- ================================================================

-- Function: Auto-log changes to ticket_history
CREATE OR REPLACE FUNCTION log_ticket_changes()
RETURNS TRIGGER AS $$
BEGIN
    -- Log status changes
    IF OLD.status IS DISTINCT FROM NEW.status THEN
        INSERT INTO ticket_history (ticket_id, changed_by, field_changed, old_value, new_value)
        VALUES (NEW.id, 'system', 'status', OLD.status, NEW.status);
    END IF;
    
    -- Log priority changes
    IF OLD.priority IS DISTINCT FROM NEW.priority THEN
        INSERT INTO ticket_history (ticket_id, changed_by, field_changed, old_value, new_value)
        VALUES (NEW.id, 'system', 'priority', OLD.priority, NEW.priority);
    END IF;
    
    -- Log subject changes
    IF OLD.subject IS DISTINCT FROM NEW.subject THEN
        INSERT INTO ticket_history (ticket_id, changed_by, field_changed, old_value, new_value)
        VALUES (NEW.id, 'system', 'subject', OLD.subject, NEW.subject);
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists
DROP TRIGGER IF EXISTS log_ticket_changes_trigger ON tickets;

-- Create trigger (runs AFTER update)
CREATE TRIGGER log_ticket_changes_trigger
    AFTER UPDATE ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION log_ticket_changes();

-- ================================================================
-- PART 8: INITIAL AUDIT ENTRY ON TICKET CREATION
-- ================================================================

-- Function: Log ticket creation
CREATE OR REPLACE FUNCTION log_ticket_creation()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO ticket_history (ticket_id, changed_by, field_changed, old_value, new_value)
    VALUES (NEW.id, 'system', 'created', NULL, 'Ticket created');
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop trigger if exists
DROP TRIGGER IF EXISTS log_ticket_creation_trigger ON tickets;

-- Create trigger (runs AFTER insert)
CREATE TRIGGER log_ticket_creation_trigger
    AFTER INSERT ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION log_ticket_creation();

-- ================================================================
-- PART 9: ROW LEVEL SECURITY (RLS)
-- ================================================================

ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;

-- Policy: Allow service role full access
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'tickets' 
        AND policyname = 'Enable access for service role'
    ) THEN
        CREATE POLICY "Enable access for service role" 
        ON tickets 
        FOR ALL 
        USING (true);
    END IF;
END $$;

-- Permissions
GRANT ALL ON tickets TO service_role;
GRANT ALL ON tickets TO anon;

-- ================================================================
-- PART 10: VERIFICATION QUERIES (Uncomment to test)
-- ================================================================

-- Test 1: Check all tables exist
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_schema = 'public' 
-- AND table_name IN ('telegram_accounts', 'tickets', 'ticket_history')
-- ORDER BY table_name;

-- Test 2: Check ticket_history structure
-- SELECT column_name, data_type, column_default 
-- FROM information_schema.columns 
-- WHERE table_name = 'ticket_history' 
-- ORDER BY ordinal_position;

-- Test 3: Check all indexes
-- SELECT tablename, indexname, indexdef 
-- FROM pg_indexes 
-- WHERE tablename IN ('tickets', 'ticket_history')
-- ORDER BY tablename, indexname;

-- Test 4: Check all triggers
-- SELECT trigger_name, event_manipulation, event_object_table, action_statement
-- FROM information_schema.triggers 
-- WHERE event_object_table IN ('tickets')
-- ORDER BY trigger_name;

-- Test 5: Check policies
-- SELECT schemaname, tablename, policyname, permissive, roles, cmd
-- FROM pg_policies 
-- WHERE tablename IN ('tickets', 'telegram_accounts', 'ticket_history')
-- ORDER BY tablename, policyname;

-- Test 6: Sample data to test triggers (OPTIONAL - run manually if needed)
-- INSERT INTO tickets (account_id, chat_id, subject, status, priority)
-- VALUES ('00000000-0000-0000-0000-000000000000', 'test123', 'Test Ticket', 'open', 'high');
--
-- UPDATE tickets SET status = 'in_progress' WHERE subject = 'Test Ticket';
-- UPDATE tickets SET priority = 'urgent' WHERE subject = 'Test Ticket';
--
-- SELECT * FROM ticket_history ORDER BY changed_at DESC LIMIT 10;

-- ================================================================
-- MIGRATION COMPLETE ✅
-- ================================================================
-- What was added in V3:
-- ✅ telegram_accounts table (if not exists)
-- ✅ tickets table with updated_at column
-- ✅ ticket_history table (NEW - audit trail)
-- ✅ Performance indexes (5 total)
-- ✅ Auto-update trigger for updated_at
-- ✅ Auto-log trigger for ticket changes (NEW)
-- ✅ Auto-log trigger for ticket creation (NEW)
-- ✅ Row Level Security enabled for all tables
-- ✅ Proper permissions granted
--
-- Features:
-- 🔹 Every ticket status/priority change is automatically logged
-- 🔹 Ticket creation is logged
-- 🔹 Full audit trail with timestamps
-- 🔹 Optimized indexes for history queries
--
-- Next Steps:
-- 1. Run verification queries above (uncomment them)
-- 2. Update backend: Add get_ticket_history() method
-- 3. Update frontend: Display history in modal
-- 4. (Optional) Add manual logging for agent-specific changes
-- ================================================================