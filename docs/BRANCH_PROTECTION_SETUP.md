# Branch Protection Setup Guide

This guide explains how to set up branch protection rules to ensure repository integrity checks are enforced.

## 🛡️ Setting up Branch Protection

### 1. Navigate to GitHub Settings

1. Go to your repository: https://github.com/mpcstudy/dreamseed_monorepo
2. Click **Settings** tab
3. Click **Branches** in the left sidebar

### 2. Add Branch Protection Rule

1. Click **Add rule** or **Add branch protection rule**
2. In **Branch name pattern**, enter: `main`
3. Configure the following settings:

#### Required Settings:
- ✅ **Require a pull request before merging**
  - ✅ **Require approvals**: 1 (or more as needed)
  - ✅ **Dismiss stale PR approvals when new commits are pushed**

- ✅ **Require status checks to pass before merging**
  - ✅ **Require branches to be up to date before merging**
  - In the search box, find and select: **Repository Integrity Check**

#### Optional Settings:
- ✅ **Require conversation resolution before merging**
- ✅ **Require signed commits** (if you use GPG signing)
- ✅ **Require linear history** (if you prefer linear history)

### 3. Save the Rule

Click **Create** to save the branch protection rule.

## 🧪 Testing Branch Protection

After setting up branch protection:

1. Create a test branch:
   ```bash
   git checkout -b test/branch-protection
   ```

2. Make a small change and commit:
   ```bash
   echo "# Test" >> TEST.md
   git add TEST.md
   git commit -m "test: branch protection"
   ```

3. Push and create a PR:
   ```bash
   git push -u origin test/branch-protection
   ```

4. Try to merge the PR - it should be blocked until:
   - The **Repository Integrity Check** workflow passes
   - Required approvals are obtained
   - All status checks are green

## 🔧 Troubleshooting

### Status Check Not Appearing

If the "Repository Integrity Check" status check doesn't appear:

1. Make sure the workflow file exists: `.github/workflows/repo-integrity.yml`
2. Push a commit to trigger the workflow
3. Check the **Actions** tab to see if the workflow ran
4. Wait a few minutes and refresh the branch protection settings

### Workflow Failing

If the repository integrity check fails:

1. Check the **Actions** tab for error details
2. Run the check locally: `./scripts/check-repo-strings.sh`
3. Fix any issues found
4. Push the fixes

## 📋 Summary

With branch protection enabled:

- ✅ All PRs must pass repository integrity checks
- ✅ No direct pushes to main branch
- ✅ Required approvals before merging
- ✅ Automatic detection of legacy repository paths
- ✅ Git remote URL verification

This ensures that repository renames and maintenance tasks are properly validated before any changes reach the main branch.
