# New Developer Onboarding Guide

Welcome to the dreamseed monorepo! This guide will help you get set up and understand our automated development workflow.

## 🚀 Quick Start (5 minutes)

### 1. Clone and Setup
```bash
# Clone the repository
git clone git@github.com:mpcstudy/dreamseed_monorepo.git
cd dreamseed_monorepo

# Set up pre-commit hooks
./scripts/setup-pre-commit.sh

# Verify setup
pre-commit run -a
```

### 2. Test Your Setup
```bash
# Test commit hook (should pass)
git commit -m "test" --allow-empty

# Check repository integrity
./scripts/check-repo-strings.sh
```

## 🎯 Understanding Our Workflow

### Automatic Features
Our repository includes several automation features that work behind the scenes:

#### 🏷️ **Automatic PR Labeling**
- PRs are automatically labeled based on changed files
- Labels help with review routing and change tracking
- Examples: `area:frontend`, `area:backend`, `type:feature`, `type:bug`

#### 👥 **Automatic Reviewer Assignment**
- Reviewers are automatically assigned based on file paths
- Defined in `CODEOWNERS` file
- Critical files require specific reviewers

#### 🔄 **Auto-Merge System**
- Add `automerge` label to automatically merge when:
  - CI passes
  - Required reviews are approved
  - No blocking labels present

#### 📦 **Dependency Management**
- Dependabot automatically creates PRs for dependency updates
- Security vulnerabilities are automatically detected
- License compliance is checked

## 📋 Development Workflow

### 1. Create a Feature Branch
```bash
# Always start from main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feat/your-feature-name
# or
git checkout -b chore/your-task-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Your Changes
```bash
# Make your changes
# Pre-commit hooks will run automatically on commit

# Stage and commit
git add .
git commit -m "feat: add new feature"

# Push your branch
git push -u origin feat/your-feature-name
```

### 3. Create a Pull Request
- Go to GitHub and create a PR
- The PR will automatically:
  - Get labeled based on changed files
  - Assign appropriate reviewers
  - Run integrity checks
  - Run security scans

### 4. Review Process
- Wait for automatic checks to pass
- Address any review feedback
- Add `automerge` label if you want automatic merging

## 🏷️ Label System

### Area Labels (What changed)
- `area:frontend` - Frontend changes
- `area:backend` - Backend changes
- `area:infra` - Infrastructure changes
- `area:docs` - Documentation changes
- `area:config` - Configuration changes
- `area:maintenance` - Repository maintenance
- `area:dependencies` - Dependency updates
- `area:security` - Security-related changes
- `area:testing` - Test changes
- `area:database` - Database changes

### Type Labels (What kind of change)
- `type:feature` - New feature
- `type:bug` - Bug fix
- `type:enhancement` - Enhancement
- `type:refactor` - Code refactoring
- `type:chore` - Maintenance task
- `type:docs` - Documentation
- `type:test` - Testing

### Status Labels (Current state)
- `status:ready-for-review` - Ready for review
- `status:in-progress` - In progress
- `status:blocked` - Blocked
- `status:needs-info` - Needs more information
- `status:automerge` - Auto-merge enabled
- `status:do-not-merge` - Do not merge

## 🔧 Troubleshooting

### Pre-commit Hooks Failing
```bash
# Run pre-commit manually to see errors
pre-commit run -a

# Fix issues and try again
git add .
git commit -m "fix: resolve pre-commit issues"
```

### Repository Integrity Check Failing
```bash
# Check for legacy repository paths
./scripts/check-repo-strings.sh

# Fix any issues found
git add .
git commit -m "fix: update repository references"
```

### Auto-merge Not Working
- Ensure all CI checks pass
- Ensure required reviews are approved
- Check for blocking labels (`do-not-merge`, `blocked`)
- Verify branch protection rules

### Too Many Dependency PRs
- Dependabot creates PRs automatically
- Review and merge as needed
- Adjust schedule in `.github/dependabot.yml` if too frequent

## 📚 Important Files to Know

### Configuration Files
- `.pre-commit-config.yaml` - Pre-commit hook configuration
- `CODEOWNERS` - Automatic reviewer assignment
- `.github/dependabot.yml` - Dependency update configuration
- `.github/labeler.yml` - Automatic labeling rules

### Scripts
- `scripts/check-repo-strings.sh` - Repository integrity check
- `scripts/setup-pre-commit.sh` - Pre-commit setup script

### Documentation
- `README.md` - Main project documentation
- `docs/OPERATIONS_HEALTHCHECK.md` - Operations guide
- `POST_RENAME.md` - Repository maintenance history

## 🎯 Best Practices

### Commit Messages
Use conventional commit format:
- `feat:` - New feature
- `fix:` - Bug fix
- `chore:` - Maintenance task
- `docs:` - Documentation
- `test:` - Testing
- `refactor:` - Code refactoring

### Branch Naming
- `feat/feature-name` - New features
- `fix/bug-description` - Bug fixes
- `chore/task-description` - Maintenance tasks
- `docs/update-description` - Documentation updates

### PR Descriptions
- Use the PR template checklist
- Describe what changed and why
- Link to related issues
- Add screenshots for UI changes

## 🆘 Getting Help

### Common Commands
```bash
# Check repository status
git status
git remote -v

# Check pre-commit status
pre-commit --version
pre-commit run -a

# Check GitHub CLI
gh --version
gh auth status

# Check repository integrity
./scripts/check-repo-strings.sh
```

### Resources
- [GitHub Documentation](https://docs.github.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Pre-commit Documentation](https://pre-commit.com/)

### Support
- Check existing GitHub Issues
- Ask in team chat
- Review this documentation
- Check the operations health check guide

---

Welcome to the team! 🎉 The automation will help you focus on coding while handling the rest automatically.
