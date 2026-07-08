-- Migration: tables required by the Supply Chain Agent
-- Run once against your Neon database before starting the agent.

-- Restock alerts log
CREATE TABLE IF NOT EXISTS restock_alerts (
    alert_id        SERIAL PRIMARY KEY,
    item_id         INTEGER NOT NULL,
    item_name       VARCHAR(255) NOT NULL,
    current_quantity NUMERIC(10, 2),
    required_quantity NUMERIC(10, 2),
    reason          TEXT,
    status          VARCHAR(50) DEFAULT 'OPEN',   -- OPEN, ACKNOWLEDGED, RESOLVED
    created_at      TIMESTAMP DEFAULT NOW(),
    resolved_at     TIMESTAMP
);

-- Purchase orders drafted by the agent
CREATE TABLE IF NOT EXISTS purchase_orders (
    po_id           SERIAL PRIMARY KEY,
    po_number       VARCHAR(100) UNIQUE NOT NULL,
    item_id         INTEGER NOT NULL,
    item_name       VARCHAR(255) NOT NULL,
    quantity        NUMERIC(10, 2) NOT NULL,
    unit            VARCHAR(50),
    supplier_name   VARCHAR(255),
    supplier_contact VARCHAR(255),
    urgency         VARCHAR(20) DEFAULT 'NORMAL',  -- URGENT, HIGH, NORMAL
    notes           TEXT,
    status          VARCHAR(50) DEFAULT 'DRAFT',   -- DRAFT, SENT, CONFIRMED, RECEIVED, CANCELLED
    created_at      TIMESTAMP DEFAULT NOW(),
    created_by      VARCHAR(100) DEFAULT 'SUPPLY_CHAIN_AGENT',
    sent_at         TIMESTAMP,
    confirmed_at    TIMESTAMP
);

-- Make sure your existing inventory table has these columns.
-- Add them if missing:
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS supplier_name    VARCHAR(255);
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS supplier_contact VARCHAR(255);
ALTER TABLE inventory ADD COLUMN IF NOT EXISTS lead_time_days   INTEGER DEFAULT 3;

-- Make sure procedure_schedule has these columns:
ALTER TABLE procedure_schedule ADD COLUMN IF NOT EXISTS required_supply_item     VARCHAR(255);
ALTER TABLE procedure_schedule ADD COLUMN IF NOT EXISTS required_supply_quantity  NUMERIC(10, 2);
