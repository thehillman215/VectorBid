-- Initialize PostgreSQL extensions for VectorBid database
-- This file runs automatically when the Docker container starts

-- UUID generation (required for primary keys)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Cryptography functions (required for password hashing)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Full-text search (useful for contract text search)
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- JSON functions (enhanced JSON/JSONB support)
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Additional indexing for performance
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Log successful extension installation
DO $$ 
BEGIN
    RAISE NOTICE 'VectorBid database extensions installed successfully:';
    RAISE NOTICE '- uuid-ossp: UUID generation';
    RAISE NOTICE '- pgcrypto: Password hashing and encryption';
    RAISE NOTICE '- pg_trgm: Full-text search capabilities';
    RAISE NOTICE '- btree_gin: Enhanced JSON indexing';
    RAISE NOTICE '- btree_gist: Advanced indexing support';
END $$;