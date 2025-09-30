# Dreamseed Monorepo

A comprehensive monorepo containing multiple services and applications.

## 🏗️ Structure

### Applications (`apps/`)
- `portal-front/` - Frontend application (Vite/React)
- `portal-api/` - Backend API service (FastAPI)

### Packages (`packages/`)
- `shared-types/` - Shared TypeScript types
- `shared-utils/` - Shared utility functions
- `shared-ui/` - Shared UI components (coming soon)

### Infrastructure
- `scripts/` - Utility scripts and automation tools
- `.github/` - GitHub Actions workflows and templates
- `docs/` - Documentation and guides

## 🚀 Quick Start

```bash
# Clone the repository
git clone git@github.com:mpcstudy/dreamseed_monorepo.git
cd dreamseed_monorepo

# Install dependencies
pnpm install

# Set up pre-commit hooks (recommended)
./scripts/setup-pre-commit.sh

# Start development
pnpm dev

# Build all packages
pnpm build

# Run tests
pnpm test
```

### Development Workflow

```bash
# Add a changeset for versioning
pnpm changeset

# Version packages (after PR merge)
pnpm version-packages

# Publish packages
pnpm release
```

## 🔧 Development Tools

### Repository Integrity Check

We maintain automated checks to ensure repository references are up-to-date:

```bash
# Check for legacy repository path references
./scripts/check-repo-strings.sh
```

This script is automatically run in:
- **Pre-commit hooks** (local development)
- **CI/CD pipelines** (GitHub Actions)
- **Branch protection rules** (PR validation)

### Pre-commit Hooks

Set up automatic checks before each commit:

```bash
# One-time setup
./scripts/setup-pre-commit.sh

# Manual run
pre-commit run --all-files
```

Pre-commit hooks will automatically:
- Check for legacy repository paths
- Verify Git remote URL
- Run standard code quality checks

### Pull Request Template

All pull requests automatically include a checklist for repository maintenance tasks, including:
- Remote URL verification
- README/Badge updates
- Branch protection review
- Secrets/Environment variables review

## 📋 Repository Maintenance

After repository renames or major changes, use the following checklist:

1. **Remote URL Update**: Verify with `git remote -v`
2. **Legacy Path Check**: Run `./scripts/check-repo-strings.sh`
3. **Documentation Update**: Update README, badges, and external links
4. **CI/CD Review**: Check workflows and secrets
5. **Branch Protection**: Review and update protection rules

### Branch Protection Setup

For complete protection, set up branch protection rules:
- See [docs/BRANCH_PROTECTION_SETUP.md](docs/BRANCH_PROTECTION_SETUP.md) for detailed instructions
- Enable "Repository Integrity Check" as a required status check
- Require PR reviews and up-to-date branches

### Operations & Maintenance

- **[Operations Health Check](docs/OPERATIONS_HEALTHCHECK.md)** - 5-minute routine to ensure all automation works
- **[New Developer Onboarding](docs/ONBOARDING_GUIDE.md)** - Complete setup guide for new team members
- **[Branch Protection Setup](docs/BRANCH_PROTECTION_SETUP.md)** - Configure branch protection rules

### Automated Workflow Features

This repository includes advanced automation:

#### 🏷️ **Automatic PR Labeling**
- PRs are automatically labeled based on changed files
- Labels include: `area:frontend`, `area:backend`, `area:infra`, etc.
- Helps with review routing and change tracking

#### 🔄 **Auto-Merge System**
- Add `automerge` label to automatically merge when:
  - CI passes
  - Required reviews are approved
  - No blocking labels present
- Uses squash merge and deletes feature branches

#### 👥 **Code Owners**
- Automatic reviewer assignment based on file paths
- Defined in `CODEOWNERS` file
- Integrates with branch protection rules

#### 🏷️ **Label Management**
- Automatic label creation and color standardization
- Consistent labeling across all PRs and issues
- Priority, type, and status labels for better organization

#### 📦 **Dependency Management**
- Automated dependency updates via Dependabot
- Security vulnerability scanning
- License compliance checking
- Automatic PR creation for updates

#### 📝 **Release Management**
- Automatic release notes generation
- Label-based changelog categorization
- Version bump automation
- Draft releases for easy publishing

#### 🧭 **Long-term Health Monitoring**
- Monthly automated health reports
- Repository metrics tracking
- Activity trend analysis
- Health indicator monitoring

#### ♻️ **Automatic Cleanup**
- Stale issues and PRs management
- Automatic labeling and notifications
- Configurable retention periods
- Smart exemption rules for critical items

#### 🏗️ **Monorepo Management**
- pnpm workspaces for efficient dependency management
- Changesets for automated versioning and releases
- Smart CI that only builds changed packages
- Shared packages for code reuse across applications

#### 🚀 **Deployment Automation**
- Environment-based deployment (staging/production)
- OIDC-based secure cloud deployments
- Multi-platform deployment support (Vercel, AWS, Railway)
- Automatic rollback and notification systems

## 🤝 Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Run the repository integrity check: `./scripts/check-repo-strings.sh`
4. Submit a pull request

The PR template will guide you through the necessary checks.

## 📄 License

[Add your license information here]
