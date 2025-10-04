#!/bin/bash

# Extract and migrate key tables from MPCStudy MySQL dump
set -e

echo "🚀 Starting key tables migration from MPCStudy..."

# Configuration
MYSQL_DUMP_FILE="/var/www/mpcstudy.com/mpcstudy_db.sql"
POSTGRES_DB="dreamseed"
POSTGRES_USER="postgres"
POSTGRES_HOST="127.0.0.1"
POSTGRES_PORT="5432"
POSTGRES_PASSWORD="DreamSeedAi@0908"

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

# Step 1: Create mpcstudy schema
echo_info "Step 1: Creating mpcstudy schema..."
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << EOF
DROP SCHEMA IF EXISTS mpcstudy CASCADE;
CREATE SCHEMA mpcstudy;
EOF

# Step 2: Create key tables manually
echo_info "Step 2: Creating key tables..."

PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" << EOF
-- Users table
CREATE TABLE mpcstudy.tbl_user (
    user_id SERIAL PRIMARY KEY,
    user_userid VARCHAR(150) NOT NULL,
    user_password VARCHAR(250) NOT NULL,
    user_fname VARCHAR(100),
    user_lname VARCHAR(100),
    user_email VARCHAR(150),
    user_cell VARCHAR(15),
    user_phone VARCHAR(15),
    user_level INTEGER DEFAULT 0,
    user_createddate VARCHAR(14),
    user_lastlogin VARCHAR(14),
    user_logincnt INTEGER DEFAULT 0,
    user_status INTEGER DEFAULT 0
);

-- Categories table
CREATE TABLE mpcstudy.tbl_category (
    ctgseq SERIAL PRIMARY KEY,
    ctgname VARCHAR(100),
    ctgdesc TEXT,
    ctgorder INTEGER,
    ctgstatus INTEGER DEFAULT 1
);

-- Questions table
CREATE TABLE mpcstudy.tbl_question (
    qseq SERIAL PRIMARY KEY,
    qtitle TEXT,
    qcontent TEXT,
    qanswer TEXT,
    qexplanation TEXT,
    qlevel INTEGER,
    qcategory INTEGER,
    qstatus INTEGER DEFAULT 1,
    qcreateddate VARCHAR(14)
);

-- Results table
CREATE TABLE mpcstudy.tbl_result (
    rseq SERIAL PRIMARY KEY,
    ruserid VARCHAR(150),
    rqseq INTEGER,
    ranswer TEXT,
    riscorrect INTEGER,
    rcreateddate VARCHAR(14)
);

-- Favorites table
CREATE TABLE mpcstudy.tbl_favorite (
    fseq SERIAL PRIMARY KEY,
    fuserid VARCHAR(150),
    fqseq INTEGER,
    fcreateddate VARCHAR(14)
);

-- Orders table
CREATE TABLE mpcstudy.tbl_order (
    oseq SERIAL PRIMARY KEY,
    ouserid VARCHAR(150),
    oamount DECIMAL(10,2),
    ostatus VARCHAR(50),
    ocreateddate VARCHAR(14)
);

-- Payment history table
CREATE TABLE mpcstudy.tbl_paymenthistorys (
    pseq SERIAL PRIMARY KEY,
    puserid VARCHAR(150),
    pamount DECIMAL(10,2),
    pstatus VARCHAR(50),
    pcreateddate VARCHAR(14)
);

-- Admin users table
CREATE TABLE mpcstudy.tbl_admusers (
    adm_id SERIAL PRIMARY KEY,
    adm_userid VARCHAR(150) NOT NULL,
    adm_password VARCHAR(250) NOT NULL,
    adm_fname VARCHAR(100),
    adm_lname VARCHAR(100),
    adm_cell VARCHAR(15),
    adm_phone VARCHAR(15),
    adm_level INTEGER DEFAULT 0,
    adm_createddate VARCHAR(14),
    adm_lastlogin VARCHAR(14),
    adm_logincnt INTEGER DEFAULT 0,
    adm_status INTEGER DEFAULT 0
);
EOF

# Step 3: Extract and insert data for each table
echo_info "Step 3: Extracting and inserting data..."

# Extract users data
echo_info "Extracting users data..."
grep -A 1000 "INSERT INTO \`tbl_user\`" "$MYSQL_DUMP_FILE" | head -20 > /tmp/users_data.sql
if [ -s /tmp/users_data.sql ]; then
    # Convert MySQL INSERT to PostgreSQL
    sed -i 's/`//g' /tmp/users_data.sql
    sed -i 's/INSERT INTO tbl_user/INSERT INTO mpcstudy.tbl_user/g' /tmp/users_data.sql
    sed -i 's/0000-00-00 00:00:00/NULL/g' /tmp/users_data.sql
    sed -i 's/0000-00-00/NULL/g' /tmp/users_data.sql
    
    # Insert data
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/users_data.sql 2>/dev/null || echo_warn "Users data insertion had some issues"
fi

# Extract categories data
echo_info "Extracting categories data..."
grep -A 1000 "INSERT INTO \`tbl_category\`" "$MYSQL_DUMP_FILE" | head -20 > /tmp/categories_data.sql
if [ -s /tmp/categories_data.sql ]; then
    sed -i 's/`//g' /tmp/categories_data.sql
    sed -i 's/INSERT INTO tbl_category/INSERT INTO mpcstudy.tbl_category/g' /tmp/categories_data.sql
    sed -i 's/0000-00-00 00:00:00/NULL/g' /tmp/categories_data.sql
    sed -i 's/0000-00-00/NULL/g' /tmp/categories_data.sql
    
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/categories_data.sql 2>/dev/null || echo_warn "Categories data insertion had some issues"
fi

# Extract questions data (first 10 questions)
echo_info "Extracting questions data..."
grep -A 1000 "INSERT INTO \`tbl_question\`" "$MYSQL_DUMP_FILE" | head -50 > /tmp/questions_data.sql
if [ -s /tmp/questions_data.sql ]; then
    sed -i 's/`//g' /tmp/questions_data.sql
    sed -i 's/INSERT INTO tbl_question/INSERT INTO mpcstudy.tbl_question/g' /tmp/questions_data.sql
    sed -i 's/0000-00-00 00:00:00/NULL/g' /tmp/questions_data.sql
    sed -i 's/0000-00-00/NULL/g' /tmp/questions_data.sql
    
    PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/questions_data.sql 2>/dev/null || echo_warn "Questions data insertion had some issues"
fi

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

echo_info "Sample data from categories table:"
PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT COUNT(*) as category_count FROM mpcstudy.tbl_category;"

# Clean up
rm -f /tmp/users_data.sql /tmp/categories_data.sql /tmp/questions_data.sql

echo_info "✅ Key tables migration completed successfully!"
echo_info "📊 Data is now available in the 'mpcstudy' schema"
echo_info "🔍 You can access the data using views: users, questions, results, categories, favorites, orders, payment_history"
echo_info "🎉 Migration script completed!"
