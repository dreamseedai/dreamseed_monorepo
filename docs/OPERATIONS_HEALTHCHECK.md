# Operations Health Check Guide

This guide provides a 5-minute routine to ensure all automation systems are working correctly.

## 🔎 5-Minute Health Check Routine

### 1. Actions Status Check
```bash
# Check recent workflow results
gh run list --limit 10

# Check repository integrity workflow logs
gh run view --log-failed --job repo-integrity

# Check all failed runs
gh run list --status failure --limit 5
```

### 2. Label Synchronization
```bash
# Manual trigger label sync (if needed)
gh workflow run labels-sync.yml
gh run watch

# Check if labels are properly created
gh label list
```

### 3. Pre-commit Local Setup Verification (New Developers)
```bash
# Test pre-commit on all files
pre-commit run -a

# Test commit hook (should pass with no changes)
git commit -m "test" --allow-empty

# Check pre-commit installation
pre-commit --version
```

### 4. Branch Protection Verification
Navigate to: **Settings → Branches → main**

Ensure the following are enabled:
- ✅ **Require PR reviews** (1 reviewer minimum)
- ✅ **Require status checks to pass**:
  - `Repository Integrity Check`
  - `Dependency Review`
  - `portal_api_ci` (if applicable)
- ✅ **Require branches to be up to date before merging**
- ✅ **Dismiss stale PR approvals when new commits are pushed**

### 5. Dependabot & Security Review
```bash
# Check Dependabot PRs
gh pr list --label "area:dependencies"

# Check security alerts
gh api repos/:owner/:repo/dependabot/alerts

# Check code scanning results
gh api repos/:owner/:repo/code-scanning/alerts
```

## 🧪 Quick Integration Rehearsal (One-time)

Test the complete workflow with a minor change:

```bash
# Create test branch
git switch -c chore/system-check

# Make minor change
echo "ping" >> .github/SYSTEM_CHECK.md

# Commit and push
git add -A && git commit -m "chore: system check"
git push -u origin chore/system-check

# Create PR and verify:
# ✅ Automatic labeling works
# ✅ Automatic reviewer assignment works
# ✅ Repository integrity check passes
# ✅ Test automerge label if needed
```

## 🛠️ Common Issues → One-Line Solutions

### Labels Not Appearing
```bash
# Check labeler.yml path patterns (root-relative, glob syntax)
gh workflow run labeler.yml
gh run watch
```

### Auto-merge Not Working
- Ensure all required status checks pass: `Repository Integrity Check`, `Dependency Review`
- Check for blocking labels: `do-not-merge`, `blocked`
- Verify branch protection rules are properly configured

### Pre-commit Too Slow
```yaml
# Add to .pre-commit-config.yaml for large hooks
- id: slow-hook
  files: 'specific-files-only'
  exclude: 'large-directories/'
  stages: [commit-msg]  # Move to commit-msg stage
```

### Too Many Dependency PRs
```yaml
# Adjust .github/dependabot.yml
schedule:
  interval: "monthly"  # Change from weekly to monthly
  day: "monday"
  time: "09:00"
```

## 🧯 Emergency Rollback (If Needed)

### Revert Recent Changes
```bash
# Revert specific commits
git revert <commit-hash>

# Restore specific files
git restore --source=<commit-hash> <file-path>

# Reset to previous state
git reset --hard <commit-hash>
```

### Temporarily Disable Branch Protection
1. Go to **Settings → Branches → main**
2. Temporarily disable protection rules
3. Fix issues
4. Re-enable protection rules

### Disable Pre-commit Hooks
```bash
# Skip hooks for emergency commits
git commit --no-verify -m "emergency fix"

# Uninstall hooks temporarily
pre-commit uninstall
```

## 📋 New Developer Onboarding Checklist

### Initial Setup
- [ ] `git clone` repository
- [ ] Run `./scripts/setup-pre-commit.sh`
- [ ] Verify: `pre-commit run -a` passes
- [ ] Test commit: `git commit -m "test" --allow-empty`

### Understanding Workflow
- [ ] Read PR template and labeling system
- [ ] Understand CODEOWNERS and review process
- [ ] Learn branch naming: `feat/*`, `chore/*`, `fix/*`
- [ ] Understand automerge label usage and requirements

### First Contribution
- [ ] Create feature branch from `main`
- [ ] Make changes and commit (pre-commit will run automatically)
- [ ] Push and create PR
- [ ] Verify automatic labeling and reviewer assignment
- [ ] Wait for CI checks to pass
- [ ] Add `automerge` label if appropriate

## 📊 Health Check Dashboard

### Daily Checks (2 minutes)
- [ ] Recent workflow runs: `gh run list --limit 5`
- [ ] Security alerts: GitHub Security tab
- [ ] Dependabot PRs: `gh pr list --label "area:dependencies"`

### Weekly Checks (5 minutes)
- [ ] Full health check routine (above)
- [ ] Label synchronization: `gh workflow run labels-sync.yml`
- [ ] Branch protection verification
- [ ] Pre-commit hook testing

### Monthly Checks (10 minutes)
- [ ] Review and update CODEOWNERS if needed
- [ ] Check and update dependency policies
- [ ] Review and optimize pre-commit configuration
- [ ] Update documentation and guides

## 🚨 Emergency Contacts

- **Repository Issues**: Check GitHub Issues
- **CI/CD Problems**: Check Actions tab
- **Security Issues**: Check Security tab
- **Dependency Issues**: Check Dependabot alerts

---

*This guide ensures your repository automation runs smoothly and helps quickly resolve common issues.*
