# Dreamseed Monorepo

A comprehensive monorepo containing multiple services and applications.

## 🏗️ Structure

- `portal_api/` - Backend API service
- `portal_front/` - Frontend application
- `scripts/` - Utility scripts and automation tools

## 🚀 Quick Start

```bash
# Clone the repository
git clone git@github.com:mpcstudy/dreamseed_monorepo.git
cd dreamseed_monorepo

# Check repository integrity
./scripts/check-repo-strings.sh
```

## 🔧 Development Tools

### Repository Integrity Check

We maintain automated checks to ensure repository references are up-to-date:

```bash
# Check for legacy repository path references
./scripts/check-repo-strings.sh
```

This script is automatically run in CI/CD pipelines to catch any hardcoded references to old repository paths.

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

## 🤝 Contributing

1. Create a feature branch from `main`
2. Make your changes
3. Run the repository integrity check: `./scripts/check-repo-strings.sh`
4. Submit a pull request

The PR template will guide you through the necessary checks.

## 📄 License

[Add your license information here]
