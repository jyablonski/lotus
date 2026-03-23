CREATE DATABASE dagster;
CREATE DATABASE mlflow;
CREATE DATABASE feast;
CREATE DATABASE pact_broker;
CREATE SCHEMA source;
CREATE SCHEMA silver;
CREATE SCHEMA gold;
SET search_path TO source;

-- uuid-ossp goes into source (same schema as the tables that use uuid_generate_v4())
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
-- vector must live in public so the type is visible regardless of search_path
CREATE EXTENSION IF NOT EXISTS vector SCHEMA public;
