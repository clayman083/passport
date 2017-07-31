BEGIN;

DROP INDEX users_email_idx;
DROP TABLE users;
DROP SEQUENCE users_pk;

COMMIT;
