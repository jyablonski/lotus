CREATE DATABASE dagster;
CREATE DATABASE mlflow;
CREATE DATABASE feast;
CREATE DATABASE pact_broker;
-- Empty DB for Django CI: migrate from scratch without colliding with docker/db seed on `postgres`.
CREATE DATABASE django_migration_ci;
CREATE SCHEMA source;
CREATE SCHEMA silver;
CREATE SCHEMA gold;
SET search_path TO source;

-- uuid-ossp should live in public so generated schema defaults like public.uuid_generate_v4() resolve.
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA public;
-- vector must live in public so the type is visible regardless of search_path
CREATE EXTENSION IF NOT EXISTS vector SCHEMA public;
