#!/bin/bash

# Simple MPCStudy MySQL → DreamSeedAI PostgreSQL Migration
# This script converts the MySQL dump to PostgreSQL format

set -e

echo "🚀 Starting simple MPCStudy to DreamSeedAI migration..."

# Configuration
MYSQL_DUMP_FILE="/var/www/mpcstudy.com/mpcstudy_db.sql"
POSTGRES_DB="dreamseed"
POSTGRES_USER="postgres"
POSTGRES_HOST="127.0.0.1"
POSTGRES_PORT="5432"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if dump file exists
if [ ! -f "$MYSQL_DUMP_FILE" ]; then
    echo_error "MySQL dump file not found: $MYSQL_DUMP_FILE"
    exit 1
fi

echo_info "Found MySQL dump file: $MYSQL_DUMP_FILE"

# Use PostgreSQL password from environment or default
POSTGRES_PASSWORD="${PGPASSWORD:-DreamSeedAi@0908}"
echo_info "Using PostgreSQL password from environment"

# Step 1: Create mpcstudy schema
echo_info "Step 1: Creating mpcstudy schema..."
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << EOF
DROP SCHEMA IF EXISTS mpcstudy CASCADE;
CREATE SCHEMA mpcstudy;
EOF

# Step 2: Convert and import key tables
echo_info "Step 2: Converting and importing key tables..."

# Convert MySQL dump to PostgreSQL format
echo_info "Converting MySQL syntax to PostgreSQL..."

# Create a converted version of the dump
sed -e 's/`//g' \
    -e 's/ENGINE=MyISAM//g' \
    -e 's/AUTO_INCREMENT/SERIAL/g' \
    -e 's/UNSIGNED//g' \
    -e 's/COLLATE utf8_general_ci//g' \
    -e 's/CHARACTER SET utf8//g' \
    -e 's/DEFAULT CHARSET=utf8//g' \
    -e 's/ENGINE=InnoDB//g' \
    -e 's/ENGINE=MyISAM//g' \
    -e 's/KEY `[^`]*`//g' \
    -e 's/UNIQUE KEY `[^`]*`//g' \
    -e 's/KEY `[^`]*`//g' \
    -e 's/COMMENT.*//g' \
    -e 's/0000-00-00 00:00:00/NULL/g' \
    -e 's/0000-00-00/NULL/g' \
    "$MYSQL_DUMP_FILE" > /tmp/mpcstudy_converted.sql

# Add schema prefix to table names
sed -i 's/CREATE TABLE /CREATE TABLE mpcstudy./g' /tmp/mpcstudy_converted.sql
sed -i 's/DROP TABLE IF EXISTS /DROP TABLE IF EXISTS mpcstudy./g' /tmp/mpcstudy_converted.sql
sed -i 's/INSERT INTO /INSERT INTO mpcstudy./g' /tmp/mpcstudy_converted.sql

# Step 3: Import the converted data
echo_info "Step 3: Importing converted data to PostgreSQL..."
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/mpcstudy_converted.sql

# Step 4: Create compatibility views
echo_info "Step 4: Creating compatibility views..."
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

# Step 5: Verify migration
echo_info "Step 5: Verifying migration..."
TABLE_COUNT=$(PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'mpcstudy';")

echo_info "Created $TABLE_COUNT tables in mpcstudy schema"

# List the tables
echo_info "Tables created:"
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT table_name FROM information_schema.tables WHERE table_schema = 'mpcstudy' ORDER BY table_name;"

# Show sample data
echo_info "Sample data from users table:"
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT COUNT(*) as user_count FROM mpcstudy.tbl_user;"

echo_info "Sample data from questions table:"
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT COUNT(*) as question_count FROM mpcstudy.tbl_question;"

# Clean up
rm -f /tmp/mpcstudy_converted.sql

echo_info "✅ Migration completed successfully!"
echo_info "📊 Data is now available in the 'mpcstudy' schema"
echo_info "🔍 You can access the data using views: users, questions, results, categories, favorites, orders, payment_history"
echo_info "🎉 Migration script completed!"
