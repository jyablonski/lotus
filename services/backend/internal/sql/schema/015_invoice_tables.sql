-- +goose Up
-- Invoice tables use UUID PKs (gen_random_uuid). If an older DB still has SERIAL
-- invoice tables from a previous revision of this migration, drop those tables
-- (or goose down to 014 and up) before applying.

CREATE TABLE IF NOT EXISTS source.invoice_senders (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    address_line1   VARCHAR(255) NOT NULL,
    address_line2   VARCHAR(255) NOT NULL DEFAULT '',
    email           VARCHAR(255) NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW() NOT NULL,
    modified_at     TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS source.invoice_clients (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(255) NOT NULL,
    address_line1   VARCHAR(255) NOT NULL,
    address_line2   VARCHAR(255) NOT NULL DEFAULT '',
    attention       VARCHAR(255) NOT NULL DEFAULT '',
    created_at      TIMESTAMP DEFAULT NOW() NOT NULL,
    modified_at     TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS source.invoice_payment_info (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    check_payable_to    VARCHAR(255) NOT NULL,
    ach_account_number  VARCHAR(50) NOT NULL,
    ach_routing_number  VARCHAR(50) NOT NULL,
    created_at          TIMESTAMP DEFAULT NOW() NOT NULL,
    modified_at         TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS source.invoices (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_number   VARCHAR(50) NOT NULL UNIQUE,
    date             DATE NOT NULL,
    due_date         DATE NOT NULL,
    terms            VARCHAR(50) NOT NULL DEFAULT 'Net 30',
    sender_id        UUID NOT NULL REFERENCES source.invoice_senders (id) ON DELETE RESTRICT,
    client_id        UUID NOT NULL REFERENCES source.invoice_clients (id) ON DELETE RESTRICT,
    payment_info_id  UUID NOT NULL REFERENCES source.invoice_payment_info (id) ON DELETE RESTRICT,
    created_at       TIMESTAMP DEFAULT NOW() NOT NULL,
    modified_at      TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS source.invoice_line_items (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id  UUID NOT NULL REFERENCES source.invoices (id) ON DELETE CASCADE,
    description TEXT NOT NULL,
    hours       NUMERIC(8, 2) NOT NULL,
    rate        NUMERIC(10, 2) NOT NULL,
    amount      NUMERIC(12, 2) NOT NULL,
    created_at  TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_invoice_line_items_invoice_id ON source.invoice_line_items (invoice_id);

-- +goose Down

DROP TABLE IF EXISTS source.invoice_line_items;
DROP TABLE IF EXISTS source.invoices;
DROP TABLE IF EXISTS source.invoice_payment_info;
DROP TABLE IF EXISTS source.invoice_clients;
DROP TABLE IF EXISTS source.invoice_senders;
