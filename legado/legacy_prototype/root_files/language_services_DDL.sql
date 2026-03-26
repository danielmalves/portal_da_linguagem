-- ============================================================
-- PostgreSQL DDL (v1) — Django + Postgres schema
-- Includes: tables, enums (as PG TYPE), constraints, indexes
-- ============================================================

-- UUID generator
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ------------------------------------------------------------
-- 1) ENUM TYPES
-- ------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'residency_t') THEN
        CREATE TYPE residency_t AS ENUM ('BR', 'FOREIGN');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'customer_type_t') THEN
        CREATE TYPE customer_type_t AS ENUM ('INDIVIDUAL', 'COMPANY');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'service_type_t') THEN
        CREATE TYPE service_type_t AS ENUM ('TRANSLATION', 'INTERPRETATION', 'REVISION');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'service_request_status_t') THEN
        CREATE TYPE service_request_status_t AS ENUM (
            'DRAFT',
            'SUBMITTED',
            'QUOTED',
            'APPROVED',
            'ASSIGNED',
            'IN_PROGRESS',
            'DELIVERED',
            'CLOSED',
            'CANCELED'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'attachment_kind_t') THEN
        CREATE TYPE attachment_kind_t AS ENUM ('SOURCE', 'REFERENCE', 'DELIVERABLE', 'OTHER');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'quote_status_t') THEN
        CREATE TYPE quote_status_t AS ENUM ('DRAFT', 'SENT', 'ACCEPTED', 'EXPIRED', 'CANCELED');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'assignment_status_t') THEN
        CREATE TYPE assignment_status_t AS ENUM (
            'INVITED',
            'ACCEPTED',
            'DECLINED',
            'IN_PROGRESS',
            'DELIVERED',
            'APPROVED'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'payment_status_t') THEN
        CREATE TYPE payment_status_t AS ENUM ('PENDING', 'CONFIRMED', 'FAILED', 'REFUNDED');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'invoice_status_t') THEN
        CREATE TYPE invoice_status_t AS ENUM ('PENDING', 'ISSUED', 'ERROR', 'CANCELED');
    END IF;

    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'nfse_status_t') THEN
        CREATE TYPE nfse_status_t AS ENUM ('SUBMITTED', 'ISSUED', 'ERROR');
    END IF;
END $$;

-- ------------------------------------------------------------
-- 2) CORE TABLES
-- ------------------------------------------------------------

-- Accounts: User
CREATE TABLE IF NOT EXISTS accounts_user (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) NOT NULL UNIQUE,
    password_hash   TEXT NOT NULL,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_staff        BOOLEAN NOT NULL DEFAULT FALSE,
    is_superuser    BOOLEAN NOT NULL DEFAULT FALSE,
    last_login      TIMESTAMPTZ NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_accounts_user_email ON accounts_user (email);

-- Customer profile (1:1 with user)
CREATE TABLE IF NOT EXISTS accounts_customer_profile (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id                     UUID NOT NULL UNIQUE REFERENCES accounts_user(id) ON DELETE CASCADE,

    residency                   residency_t NOT NULL,
    customer_type               customer_type_t NOT NULL,
    legal_name                  VARCHAR(255) NOT NULL,
    country                     CHAR(2) NOT NULL,
    phone                       VARCHAR(30) NULL,

    tax_id_br                   VARCHAR(20) NULL,  -- CPF/CNPJ
    foreign_tax_id              VARCHAR(50) NULL,
    foreign_tax_id_type         VARCHAR(30) NULL,  -- VAT/NIF/EIN/PASSPORT/OTHER
    foreign_tax_id_absent_reason TEXT NULL,

    address_line1               VARCHAR(255) NOT NULL,
    address_line2               VARCHAR(255) NULL,
    city                        VARCHAR(100) NOT NULL,
    region                      VARCHAR(100) NULL,
    postal_code                 VARCHAR(20) NULL,

    created_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_customer_taxid_by_residency
        CHECK (
            (residency = 'BR' AND tax_id_br IS NOT NULL)
            OR
            (residency = 'FOREIGN')
        )
);

CREATE INDEX IF NOT EXISTS idx_customer_residency ON accounts_customer_profile (residency);
CREATE INDEX IF NOT EXISTS idx_customer_type ON accounts_customer_profile (customer_type);
CREATE INDEX IF NOT EXISTS idx_customer_country ON accounts_customer_profile (country);
CREATE INDEX IF NOT EXISTS idx_customer_tax_id_br ON accounts_customer_profile (tax_id_br);
CREATE INDEX IF NOT EXISTS idx_customer_foreign_tax_id ON accounts_customer_profile (foreign_tax_id);

-- Linguist profile (1:1 with user)
CREATE TABLE IF NOT EXISTS accounts_linguist_profile (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL UNIQUE REFERENCES accounts_user(id) ON DELETE CASCADE,

    timezone    VARCHAR(50) NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,

    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_linguist_active ON accounts_linguist_profile (is_active);

-- Linguist language pairs
CREATE TABLE IF NOT EXISTS accounts_language_pair (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    linguist_id UUID NOT NULL REFERENCES accounts_linguist_profile(id) ON DELETE CASCADE,
    source_lang CHAR(5) NOT NULL,
    target_lang CHAR(5) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_linguist_lang_pair UNIQUE (linguist_id, source_lang, target_lang)
);

CREATE INDEX IF NOT EXISTS idx_lang_pair_linguist ON accounts_language_pair (linguist_id);
CREATE INDEX IF NOT EXISTS idx_lang_pair_source ON accounts_language_pair (source_lang);
CREATE INDEX IF NOT EXISTS idx_lang_pair_target ON accounts_language_pair (target_lang);

-- ------------------------------------------------------------
-- 3) ORDERS / REQUESTS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS orders_service_request (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id      UUID NOT NULL REFERENCES accounts_customer_profile(id) ON DELETE RESTRICT,

    service_type     service_type_t NOT NULL,
    source_lang      CHAR(5) NOT NULL,
    target_lang      CHAR(5) NOT NULL,
    subject_area     VARCHAR(100) NULL,

    deadline_at      TIMESTAMPTZ NOT NULL,
    instructions     TEXT NULL,

    status           service_request_status_t NOT NULL DEFAULT 'DRAFT',

    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_request_customer_created ON orders_service_request (customer_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_request_status_updated ON orders_service_request (status, updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_request_deadline ON orders_service_request (deadline_at);
CREATE INDEX IF NOT EXISTS idx_request_service_type ON orders_service_request (service_type);
CREATE INDEX IF NOT EXISTS idx_request_langs ON orders_service_request (source_lang, target_lang);

-- Optional internal thread/messages
CREATE TABLE IF NOT EXISTS orders_request_message (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_request_id   UUID NOT NULL REFERENCES orders_service_request(id) ON DELETE CASCADE,
    author_user_id       UUID NOT NULL REFERENCES accounts_user(id) ON DELETE RESTRICT,
    body                TEXT NOT NULL,
    created_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_reqmsg_request ON orders_request_message (service_request_id, created_at);
CREATE INDEX IF NOT EXISTS idx_reqmsg_author ON orders_request_message (author_user_id);

-- ------------------------------------------------------------
-- 4) STAFFING (Assignments)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS staffing_assignment (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_request_id   UUID NOT NULL REFERENCES orders_service_request(id) ON DELETE CASCADE,
    linguist_id          UUID NOT NULL REFERENCES accounts_linguist_profile(id) ON DELETE RESTRICT,

    assignment_type      service_type_t NOT NULL,
    status              assignment_status_t NOT NULL DEFAULT 'INVITED',

    deadline_at          TIMESTAMPTZ NOT NULL,
    instructions         TEXT NULL,

    agreed_rate_snapshot JSONB NULL,

    created_at           TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_assignment_request_status ON staffing_assignment (service_request_id, status);
CREATE INDEX IF NOT EXISTS idx_assignment_linguist_status ON staffing_assignment (linguist_id, status);
CREATE INDEX IF NOT EXISTS idx_assignment_deadline ON staffing_assignment (deadline_at);

-- ------------------------------------------------------------
-- 5) FILES / ATTACHMENTS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS files_attachment (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    service_request_id   UUID NULL REFERENCES orders_service_request(id) ON DELETE CASCADE,
    assignment_id        UUID NULL REFERENCES staffing_assignment(id) ON DELETE CASCADE,
    uploaded_by_user_id  UUID NOT NULL REFERENCES accounts_user(id) ON DELETE RESTRICT,

    kind                attachment_kind_t NOT NULL,
    storage_key         TEXT NOT NULL,
    original_filename   VARCHAR(255) NOT NULL,
    content_type        VARCHAR(100) NULL,
    size_bytes          BIGINT NULL,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_attachment_exactly_one_parent
        CHECK (
            (service_request_id IS NOT NULL AND assignment_id IS NULL)
            OR
            (service_request_id IS NULL AND assignment_id IS NOT NULL)
        )
);

CREATE INDEX IF NOT EXISTS idx_attachment_request ON files_attachment (service_request_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_attachment_assignment ON files_attachment (assignment_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_attachment_kind ON files_attachment (kind);
CREATE INDEX IF NOT EXISTS idx_attachment_uploader ON files_attachment (uploaded_by_user_id);

-- ------------------------------------------------------------
-- 6) QUOTES
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS quotes_quote (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_request_id   UUID NOT NULL UNIQUE REFERENCES orders_service_request(id) ON DELETE CASCADE,

    currency            CHAR(3) NOT NULL,
    amount_total        NUMERIC(12,2) NOT NULL,

    breakdown_json      JSONB NULL,
    valid_until         TIMESTAMPTZ NOT NULL,

    status              quote_status_t NOT NULL DEFAULT 'DRAFT',

    accepted_at         TIMESTAMPTZ NULL,
    terms_snapshot      TEXT NULL,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_quote_status ON quotes_quote (status);
CREATE INDEX IF NOT EXISTS idx_quote_valid_until ON quotes_quote (valid_until);
CREATE INDEX IF NOT EXISTS idx_quote_accepted_at ON quotes_quote (accepted_at);

-- ------------------------------------------------------------
-- 7) PAYMENTS
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS payments_payment (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_request_id   UUID NOT NULL REFERENCES orders_service_request(id) ON DELETE CASCADE,

    provider            VARCHAR(50) NOT NULL,
    provider_reference  VARCHAR(100) NOT NULL,
    status              payment_status_t NOT NULL DEFAULT 'PENDING',

    amount              NUMERIC(12,2) NOT NULL,
    currency            CHAR(3) NOT NULL,

    confirmed_at        TIMESTAMPTZ NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_payment_provider_reference UNIQUE (provider, provider_reference)
);

CREATE INDEX IF NOT EXISTS idx_payment_request_status ON payments_payment (service_request_id, status);
CREATE INDEX IF NOT EXISTS idx_payment_confirmed_at ON payments_payment (confirmed_at);
CREATE INDEX IF NOT EXISTS idx_payment_provider ON payments_payment (provider);

-- Webhook events (optional but recommended)
CREATE TABLE IF NOT EXISTS payments_webhook_event (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider            VARCHAR(50) NOT NULL,
    event_type          VARCHAR(80) NOT NULL,
    provider_event_id   VARCHAR(120) NULL,
    payload_json        JSONB NOT NULL,
    received_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    processed_at        TIMESTAMPTZ NULL,
    processing_status   VARCHAR(20) NOT NULL DEFAULT 'PENDING', -- PENDING|PROCESSED|FAILED
    error_message       TEXT NULL
);

-- If provider_event_id exists, it can be unique to dedupe
CREATE UNIQUE INDEX IF NOT EXISTS uq_webhook_provider_event
    ON payments_webhook_event (provider, provider_event_id)
    WHERE provider_event_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_webhook_provider_received ON payments_webhook_event (provider, received_at DESC);
CREATE INDEX IF NOT EXISTS idx_webhook_processing_status ON payments_webhook_event (processing_status);

-- ------------------------------------------------------------
-- 8) BILLING / NFS-e
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS billing_invoice (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_request_id   UUID NOT NULL UNIQUE REFERENCES orders_service_request(id) ON DELETE CASCADE,

    amount              NUMERIC(12,2) NOT NULL,
    currency            CHAR(3) NOT NULL,

    status              invoice_status_t NOT NULL DEFAULT 'PENDING',
    issued_at           TIMESTAMPTZ NULL,

    customer_snapshot_json JSONB NULL,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_invoice_status ON billing_invoice (status);
CREATE INDEX IF NOT EXISTS idx_invoice_issued_at ON billing_invoice (issued_at);

CREATE TABLE IF NOT EXISTS billing_nfse_record (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    invoice_id           UUID NOT NULL UNIQUE REFERENCES billing_invoice(id) ON DELETE CASCADE,

    provider            VARCHAR(50) NOT NULL,
    protocol            VARCHAR(100) NULL,
    nfse_number         VARCHAR(100) NULL,

    status              nfse_status_t NOT NULL DEFAULT 'SUBMITTED',

    pdf_storage_key     TEXT NULL,
    xml_storage_key     TEXT NULL,

    error_message       TEXT NULL,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_nfse_provider ON billing_nfse_record (provider);
CREATE INDEX IF NOT EXISTS idx_nfse_protocol ON billing_nfse_record (protocol);
CREATE INDEX IF NOT EXISTS idx_nfse_number ON billing_nfse_record (nfse_number);
CREATE INDEX IF NOT EXISTS idx_nfse_status ON billing_nfse_record (status);

-- ------------------------------------------------------------
-- NOTE: Django will usually manage migrations; this DDL is
-- for documentation/prototyping/import. Consider adding
-- triggers to auto-update updated_at if you want pure SQL.
-- ------------------------------------------------------------
