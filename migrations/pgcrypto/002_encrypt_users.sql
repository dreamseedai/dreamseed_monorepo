-- Template to migrate plaintext columns to encrypted form using pgcrypto
-- NOTE: Do NOT hardcode encryption keys in SQL. Pass keys from the application at runtime.
-- This template assumes an existing table `users` with columns: id (pk), name, email, phone (optional).
-- It creates new encrypted columns and backfills using a placeholder function call.

BEGIN;

-- 1) Add encrypted columns (bytea) and hashed columns for lookup
ALTER TABLE users
    ADD COLUMN IF NOT EXISTS name_enc  bytea,
    ADD COLUMN IF NOT EXISTS email_enc bytea,
    ADD COLUMN IF NOT EXISTS phone_enc bytea,
    ADD COLUMN IF NOT EXISTS email_hash bytea,
    ADD COLUMN IF NOT EXISTS phone_hash bytea;

-- 2) Backfill encryption using a session key placeholder
-- Replace ':{enc_key}' at runtime using your migration runner, or backfill from application code.
-- Symmetric example: pgp_sym_encrypt(text, key, 'cipher-algo=aes256')
UPDATE users
SET
    name_enc  = CASE WHEN name  IS NOT NULL THEN pgp_sym_encrypt(name::text,  :enc_key, 'cipher-algo=aes256') ELSE NULL END,
    email_enc = CASE WHEN email IS NOT NULL THEN pgp_sym_encrypt(email::text, :enc_key, 'cipher-algo=aes256') ELSE NULL END,
    phone_enc = CASE WHEN phone IS NOT NULL THEN pgp_sym_encrypt(phone::text, :enc_key, 'cipher-algo=aes256') ELSE NULL END,
    email_hash = CASE WHEN email IS NOT NULL THEN digest(lower(email)::bytea, 'sha256') ELSE NULL END,
    phone_hash = CASE WHEN phone IS NOT NULL THEN digest(regexp_replace(phone, '\\D', '', 'g')::bytea, 'sha256') ELSE NULL END
WHERE (name_enc IS NULL AND name IS NOT NULL)
   OR (email_enc IS NULL AND email IS NOT NULL)
   OR (phone_enc IS NULL AND phone IS NOT NULL);

-- 3) Create indexes for hashed lookups (case-insensitive email, normalized phone)
CREATE INDEX IF NOT EXISTS idx_users_email_hash ON users (email_hash);
CREATE INDEX IF NOT EXISTS idx_users_phone_hash ON users (phone_hash);

-- 4) (Optional) Drop plaintext columns after verifying application reads encrypted fields
-- ALTER TABLE users DROP COLUMN name, DROP COLUMN email, DROP COLUMN phone;

COMMIT;
