# pgcrypto column encryption templates

This folder contains SQL templates to enable `pgcrypto` and migrate plaintext columns to encrypted form.

- `001_enable_pgcrypto.sql` — enables the extension
- `002_encrypt_users.sql` — adds encrypted columns (`*_enc`), backfills them with `pgp_sym_encrypt`, and creates SHA-256 hashes for lookup

## Key handling
- Do not embed keys in SQL. Pass keys from your migration runner (e.g., psql variable, Flyway/Liquibase parameters) or perform the backfill from application code.
- Example (psql):
  - `\set enc_key 'YOUR-KEY-MATERIAL'`
  - Replace `:enc_key` placeholder via your runner; psql supports `:enc_key` substitution only for `\gexec`/`PREPARE` usage. Alternatively, run the UPDATE from application code.

## Application usage
- Write:
  - `INSERT ... name_enc = pgp_sym_encrypt(:name, :enc_key, 'cipher-algo=aes256')`
- Read:
  - `SELECT convert_from(pgp_sym_decrypt(name_enc, :enc_key), 'UTF8') AS name ...`
- Lookup by email/phone:
  - Store `email_hash = digest(lower(email)::bytea, 'sha256')`
  - `SELECT ... WHERE email_hash = digest(lower(:email)::bytea, 'sha256')`

## Deployment steps (suggested)
1) Run `001_enable_pgcrypto.sql`
2) Add encrypted + hash columns via `002_encrypt_users.sql` without dropping plaintext
3) Update application to use encrypted columns for writes/reads and maintain `*_hash`
4) Verify for a period, then drop plaintext columns
5) Rotate keys periodically by re-encrypting in batches
