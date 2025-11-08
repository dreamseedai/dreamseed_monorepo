#\!/usr/bin/env bash
set -euo pipefail

# Production Rollback: attempt VIEW V1 Schema Lock
# Last Updated: 2025-11-01

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

confirm() {
    read -p "$(echo -e ${YELLOW}[CONFIRM]${NC}) $1 (yes/no): " response
    [[ "$response" == "yes" ]]
}

rollback_alembic() {
    log_info "=== Rollback Method 1: Alembic Downgrade ==="
    
    log_warn "This will downgrade to previous revision"
    log_warn "The attempt VIEW will be dropped\!"
    
    if \! confirm "Proceed with alembic downgrade?"; then
        log_error "Aborted by user"
        exit 1
    fi
    
    cd apps/seedtest_api
    
    log_info "Current revision:"
    alembic current
    
    log_info "Downgrading..."
    alembic downgrade -1
    
    log_info "New revision:"
    alembic current
    
    log_info "✅ Alembic rollback completed"
}

rollback_backup() {
    log_info "=== Rollback Method 2: Database Backup Restore ==="
    
    log_error "⚠️  WARNING: This will restore the entire database\!"
    log_error "All data changes since backup will be lost\!"
    
    if \! confirm "Do you have a backup file ready?"; then
        log_error "Backup file required. Aborting."
        exit 1
    fi
    
    read -p "Enter backup file path: " backup_file
    
    if [[ ! -f "$backup_file" ]]; then
        log_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    log_warn "Backup file: $backup_file"
    log_warn "Target database: $DATABASE_URL"
    
    if \! confirm "Proceed with restore? THIS CANNOT BE UNDONE\!"; then
        log_error "Aborted by user"
        exit 1
    fi
    
    log_info "Restoring database..."
    pg_restore -d "$DATABASE_URL" --clean --if-exists "$backup_file"
    
    log_info "✅ Database restore completed"
}

main() {
    log_error "========================================="
    log_error "⚠️  PRODUCTION ROLLBACK"
    log_error "========================================="
    echo
    
    if [[ -z "${DATABASE_URL:-}" ]]; then
        log_error "DATABASE_URL not set"
        exit 1
    fi
    
    echo "Select rollback method:"
    echo "  1) Alembic downgrade (recommended)"
    echo "  2) Database backup restore (full restore)"
    echo
    
    read -p "Enter choice (1 or 2): " choice
    
    case $choice in
        1)
            rollback_alembic
            ;;
        2)
            rollback_backup
            ;;
        *)
            log_error "Invalid choice"
            exit 1
            ;;
    esac
    
    echo
    log_info "========================================="
    log_info "Rollback completed"
    log_info "========================================="
    log_warn "Next steps:"
    echo "  1. Verify application health"
    echo "  2. Check error logs"
    echo "  3. Notify team of rollback"
    echo "  4. Investigate root cause"
}

main "$@"
