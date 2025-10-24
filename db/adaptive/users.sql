DROP TABLE IF EXISTS users CASCADE;
CREATE TABLE users (
  user_id         SERIAL PRIMARY KEY,
  email           VARCHAR(100) UNIQUE NOT NULL,
  password_hash   VARCHAR(200) NOT NULL,
  name            VARCHAR(100),
  role            VARCHAR(20) NOT NULL,
  organization_id INT REFERENCES organizations(org_id)
);

