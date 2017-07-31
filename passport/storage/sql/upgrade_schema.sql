-- SET ROLE 'passport';

BEGIN;

CREATE SEQUENCE IF NOT EXISTS users_pk START WITH 1;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY default nextval('users_pk'),
    email VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP WITHOUT TIME ZONE,
    created_on TIMESTAMP WITHOUT TIME ZONE
);

CREATE UNIQUE INDEX IF NOT EXISTS users_email_idx ON users (email);

COMMIT;
