#!/bin/bash

# MPCStudy MySQL → DreamSeedAI PostgreSQL Migration Script
# Usage: ./migrate-mpcstudy-to-dreamseed.sh

set -e

echo "🚀 Starting MPCStudy to DreamSeedAI database migration..."

# Configuration
MYSQL_DUMP_FILE="/var/www/mpcstudy.com/mpcstudy_db.sql"
MYSQL_DB_NAME="mpcstudy_db"
MYSQL_USER="mpcstudy_root"
POSTGRES_DB="dreamseed"
POSTGRES_USER="postgres"
POSTGRES_HOST="127.0.0.1"
POSTGRES_PORT="5432"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if MySQL dump file exists
if [ ! -f "$MYSQL_DUMP_FILE" ]; then
    echo_error "MySQL dump file not found: $MYSQL_DUMP_FILE"
    exit 1
fi

echo_info "Found MySQL dump file: $MYSQL_DUMP_FILE"

# Step 1: Create temporary MySQL database for conversion
echo_info "Step 1: Setting up temporary MySQL database..."

# Ask for MySQL password
echo "Enter MySQL password for user '$MYSQL_USER':"
read -s MYSQL_PASSWORD

# Create temporary database
mysql -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "CREATE DATABASE IF NOT EXISTS mpcstudy_temp;"

# Import the dump into temporary database
echo_info "Importing MySQL dump into temporary database..."
mysql -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" mpcstudy_temp < "$MYSQL_DUMP_FILE"

# Step 2: Convert MySQL to PostgreSQL using pgloader
echo_info "Step 2: Converting MySQL to PostgreSQL..."

# Check if pgloader is installed
if ! command -v pgloader &> /dev/null; then
    echo_warn "pgloader not found. Installing pgloader..."
    sudo apt-get update
    sudo apt-get install -y pgloader
fi

# Ask for PostgreSQL password
echo "Enter PostgreSQL password for user '$POSTGRES_USER':"
read -s POSTGRES_PASSWORD

# Create pgloader configuration
cat > /tmp/mpcstudy_migration.load << EOF
LOAD DATABASE
    FROM mysql://$MYSQL_USER:$MYSQL_PASSWORD@localhost/mpcstudy_temp
    INTO postgresql://$POSTGRES_USER:$POSTGRES_PASSWORD@$POSTGRES_HOST:$POSTGRES_PORT/$POSTGRES_DB

WITH include drop, create tables, create indexes, reset sequences

SET work_mem to '256MB',
    maintenance_work_mem to '512 MB'

CAST type datetime to timestamp drop default drop not null,
     type date drop not null drop default using zero-dates-to-null,
     type tinyint to smallint drop typemod,
     type float to float drop typemod,
     type double to double precision drop typemod

BEFORE LOAD DO
\$\$ DROP SCHEMA IF EXISTS mpcstudy CASCADE; \$\$,
\$\$ CREATE SCHEMA mpcstudy; \$\$;
EOF

# Run pgloader
echo_info "Running pgloader conversion..."
pgloader /tmp/mpcstudy_migration.load

# Step 3: Clean up temporary database
echo_info "Step 3: Cleaning up temporary MySQL database..."
mysql -u "$MYSQL_USER" -p"$MYSQL_PASSWORD" -e "DROP DATABASE IF EXISTS mpcstudy_temp;"

# Step 4: Verify migration
echo_info "Step 4: Verifying migration..."

# Check if tables were created
TABLE_COUNT=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'mpcstudy';")

echo_info "Created $TABLE_COUNT tables in mpcstudy schema"

# List the tables
echo_info "Tables created:"
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'mpcstudy' ORDER BY table_name;"

# Step 5: Create views for compatibility
echo_info "Step 5: Creating compatibility views..."

PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << EOF
-- Create views for easier access
CREATE OR REPLACE VIEW users AS 
SELECT * FROM mpcstudy.tbl_user;

CREATE OR REPLACE VIEW questions AS 
SELECT * FROM mpcstudy.tbl_question;

CREATE OR REPLACE VIEW results AS 
SELECT * FROM mpcstudy.tbl_result;

CREATE OR REPLACE VIEW categories AS 
SELECT * FROM mpcstudy.tbl_category;

CREATE OR REPLACE VIEW favorites AS 
SELECT * FROM mpcstudy.tbl_favorite;

CREATE OR REPLACE VIEW orders AS 
SELECT * FROM mpcstudy.tbl_order;

CREATE OR REPLACE VIEW payment_history AS 
SELECT * FROM mpcstudy.tbl_paymenthistorys;

-- Grant permissions
GRANT USAGE ON SCHEMA mpcstudy TO postgres;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA mpcstudy TO postgres;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA mpcstudy TO postgres;
EOF

echo_info "✅ Migration completed successfully!"
echo_info "📊 Data is now available in the 'mpcstudy' schema"
echo_info "🔍 You can access the data using views: users, questions, results, categories, favorites, orders, payment_history"

# Clean up
rm -f /tmp/mpcstudy_migration.load

echo_info "🎉 Migration script completed!"
