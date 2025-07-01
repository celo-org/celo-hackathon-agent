-- PostgreSQL initialization script for AI Project Analyzer

-- Create additional databases
CREATE DATABASE analyzer_test_db;
CREATE DATABASE analyzer_integration_db;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Create custom user (if needed)
-- CREATE USER analyzer_user WITH PASSWORD 'analyzer_password';
-- GRANT ALL PRIVILEGES ON DATABASE analyzer_db TO analyzer_user;
-- GRANT ALL PRIVILEGES ON DATABASE analyzer_test_db TO analyzer_user;

-- Performance tuning
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_duration = on;
ALTER SYSTEM SET log_min_duration_statement = 1000;

-- Restart required for some settings
-- SELECT pg_reload_conf(); 