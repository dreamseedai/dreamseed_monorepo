#!/usr/bin/env bash
set -euo pipefail

# CI/CD Configuration Validation Script
# This script validates all CI/CD configurations and dependencies

echo "🔍 Validating CI/CD Configuration..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "SUCCESS")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "WARNING")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "ERROR")
            echo -e "${RED}❌ $message${NC}"
            ;;
    esac
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to validate YAML syntax
validate_yaml() {
    local file=$1
    if command_exists yamllint; then
        if yamllint "$file" >/dev/null 2>&1; then
            print_status "SUCCESS" "YAML syntax valid: $file"
        else
            print_status "ERROR" "YAML syntax invalid: $file"
            return 1
        fi
    else
        print_status "WARNING" "yamllint not found, skipping YAML validation for $file"
    fi
}

# Function to validate Ansible playbooks
validate_ansible() {
    local playbook=$1
    if command_exists ansible-playbook; then
        if ansible-playbook --syntax-check "$playbook" >/dev/null 2>&1; then
            print_status "SUCCESS" "Ansible playbook valid: $playbook"
        else
            print_status "ERROR" "Ansible playbook invalid: $playbook"
            return 1
        fi
    else
        print_status "WARNING" "ansible-playbook not found, skipping Ansible validation for $playbook"
    fi
}

# Function to validate GitHub Actions workflow
validate_github_workflow() {
    local workflow=$1
    if command_exists actionlint; then
        if actionlint "$workflow" >/dev/null 2>&1; then
            print_status "SUCCESS" "GitHub Actions workflow valid: $workflow"
        else
            print_status "ERROR" "GitHub Actions workflow invalid: $workflow"
            return 1
        fi
    else
        print_status "WARNING" "actionlint not found, skipping GitHub Actions validation for $workflow"
    fi
}

# Function to check required secrets
check_secrets() {
    local secrets_file=$1
    if [ -f "$secrets_file" ]; then
        print_status "SUCCESS" "Secrets file found: $secrets_file"
        # Check if all required secrets are present
        local required_secrets=("SLACK_BOT_TOKEN" "SLACK_CHANNEL_ID" "SSH_PRIVATE_KEY" "VAULT_ADDR")
        for secret in "${required_secrets[@]}"; do
            if grep -q "$secret" "$secrets_file"; then
                print_status "SUCCESS" "Required secret found: $secret"
            else
                print_status "WARNING" "Required secret missing: $secret"
            fi
        done
    else
        print_status "WARNING" "Secrets file not found: $secrets_file"
    fi
}

# Function to validate Docker configuration
validate_docker() {
    local dockerfile=$1
    if [ -f "$dockerfile" ]; then
        if command_exists docker; then
            if docker build --no-cache -f "$dockerfile" . >/dev/null 2>&1; then
                print_status "SUCCESS" "Docker build successful: $dockerfile"
            else
                print_status "ERROR" "Docker build failed: $dockerfile"
                return 1
            fi
        else
            print_status "WARNING" "Docker not found, skipping Docker validation for $dockerfile"
        fi
    else
        print_status "WARNING" "Dockerfile not found: $dockerfile"
    fi
}

# Function to validate Node.js configuration
validate_nodejs() {
    local package_json=$1
    if [ -f "$package_json" ]; then
        if command_exists npm; then
            if npm ci --dry-run >/dev/null 2>&1; then
                print_status "SUCCESS" "Node.js dependencies valid: $package_json"
            else
                print_status "ERROR" "Node.js dependencies invalid: $package_json"
                return 1
            fi
        else
            print_status "WARNING" "npm not found, skipping Node.js validation for $package_json"
        fi
    else
        print_status "WARNING" "package.json not found: $package_json"
    fi
}

# Function to validate Python configuration
validate_python() {
    local requirements_file=$1
    if [ -f "$requirements_file" ]; then
        if command_exists pip; then
            if pip check >/dev/null 2>&1; then
                print_status "SUCCESS" "Python dependencies valid: $requirements_file"
            else
                print_status "ERROR" "Python dependencies invalid: $requirements_file"
                return 1
            fi
        else
            print_status "WARNING" "pip not found, skipping Python validation for $requirements_file"
        fi
    else
        print_status "WARNING" "requirements.txt not found: $requirements_file"
    fi
}

# Function to validate Go configuration
validate_go() {
    local go_mod=$1
    if [ -f "$go_mod" ]; then
        if command_exists go; then
            if go mod verify >/dev/null 2>&1; then
                print_status "SUCCESS" "Go modules valid: $go_mod"
            else
                print_status "ERROR" "Go modules invalid: $go_mod"
                return 1
            fi
        else
            print_status "WARNING" "go not found, skipping Go validation for $go_mod"
        fi
    else
        print_status "WARNING" "go.mod not found: $go_mod"
    fi
}

# Main validation function
main() {
    local errors=0
    local warnings=0

    echo "🔍 Starting CI/CD configuration validation..."

    # Check required tools
    echo "📋 Checking required tools..."
    local required_tools=("git" "curl" "jq")
    for tool in "${required_tools[@]}"; do
        if command_exists "$tool"; then
            print_status "SUCCESS" "Required tool found: $tool"
        else
            print_status "ERROR" "Required tool missing: $tool"
            ((errors++))
        fi
    done

    # Validate GitHub Actions workflows
    echo "🔧 Validating GitHub Actions workflows..."
    for workflow in .github/workflows/*.yml; do
        if [ -f "$workflow" ]; then
            validate_yaml "$workflow" || ((errors++))
            validate_github_workflow "$workflow" || ((warnings++))
        fi
    done

    # Validate GitLab CI configuration
    echo "🔧 Validating GitLab CI configuration..."
    if [ -f ".gitlab-ci.yml" ]; then
        validate_yaml ".gitlab-ci.yml" || ((errors++))
    else
        print_status "WARNING" "GitLab CI configuration not found"
        ((warnings++))
    fi

    # Validate Ansible playbooks
    echo "🔧 Validating Ansible playbooks..."
    for playbook in ansible/playbooks/*.yaml; do
        if [ -f "$playbook" ]; then
            validate_yaml "$playbook" || ((errors++))
            validate_ansible "$playbook" || ((errors++))
        fi
    done

    # Validate Docker configuration
    echo "🔧 Validating Docker configuration..."
    for dockerfile in */Dockerfile; do
        if [ -f "$dockerfile" ]; then
            validate_docker "$dockerfile" || ((errors++))
        fi
    done

    # Validate Node.js configuration
    echo "🔧 Validating Node.js configuration..."
    for package_json in */package.json; do
        if [ -f "$package_json" ]; then
            validate_nodejs "$package_json" || ((errors++))
        fi
    done

    # Validate Python configuration
    echo "🔧 Validating Python configuration..."
    for requirements_file in */requirements.txt; do
        if [ -f "$requirements_file" ]; then
            validate_python "$requirements_file" || ((errors++))
        fi
    done

    # Validate Go configuration
    echo "🔧 Validating Go configuration..."
    for go_mod in */go.mod; do
        if [ -f "$go_mod" ]; then
            validate_go "$go_mod" || ((errors++))
        fi
    done

    # Check secrets configuration
    echo "🔐 Checking secrets configuration..."
    check_secrets "secrets.env" || ((warnings++))
    check_secrets ".env" || ((warnings++))

    # Summary
    echo "📊 Validation Summary:"
    echo "  Errors: $errors"
    echo "  Warnings: $warnings"

    if [ $errors -eq 0 ]; then
        print_status "SUCCESS" "All validations passed! 🎉"
        exit 0
    else
        print_status "ERROR" "Validation failed with $errors errors"
        exit 1
    fi
}

# Run main function
main "$@"