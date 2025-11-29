#!/bin/bash
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PostgreSQL Initialization Script
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 
# This script runs automatically when the PostgreSQL container
# is created for the first time.
#
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 PostgreSQL Initialization"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Create test database
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    -- Create test database for E2E tests
    CREATE DATABASE dreamseed_test;
    GRANT ALL PRIVILEGES ON DATABASE dreamseed_test TO $POSTGRES_USER;
    
    -- Enable extensions if needed
    \c $POSTGRES_DB
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    
    \c dreamseed_test
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
EOSQL

echo "✅ PostgreSQL initialization complete!"
echo "   - Main database: $POSTGRES_DB"
echo "   - Test database: dreamseed_test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
