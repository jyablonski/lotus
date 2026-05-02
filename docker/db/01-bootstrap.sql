CREATE DATABASE dagster;
CREATE DATABASE mlflow;
CREATE DATABASE feast;
CREATE DATABASE pact_broker;
-- Empty DB for django CI validation; separate from seeded `postgres`.
CREATE DATABASE django_migration_ci;
CREATE SCHEMA source;
CREATE SCHEMA silver;
CREATE SCHEMA gold;
SET search_path TO source;

-- uuid-ossp should live in public so generated schema defaults like public.uuid_generate_v4() resolve.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA public;
-- vector must live in public so the type is visible regardless of search_path
CREATE EXTENSION IF NOT EXISTS vector SCHEMA public;

-- create source schema in django migration ci database so it can run migrations
\connect django_migration_ci
CREATE SCHEMA IF NOT EXISTS source;
