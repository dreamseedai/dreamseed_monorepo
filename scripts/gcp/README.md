# GCP Environment Audit Script

This directory contains scripts for auditing and validating GCP infrastructure configuration.

## env_audit.sh

Validates the alignment between:
- GCP Project settings
- GitHub Repository Variables
- GKE cluster configuration
- Workload Identity Federation (WIF) setup

### Prerequisites

- `gcloud` CLI installed and authenticated
- `kubectl` (optional, for deeper cluster checks)
- `jq` (for JSON parsing)

### Required Environment Variables

The script checks for the following variables (can be set in environment or as GitHub repo variables):

| Variable | Description | Example |
|----------|-------------|---------|
| `GCP_PROJECT_ID` | GCP project ID | `univprepai` |
| `GKE_CLUSTER` | GKE cluster name | `seedtest-main` |
| `GKE_LOCATION` | Cluster location (region or zone) | `asia-northeast3` |
| `GCP_WIF_SERVICE_ACCOUNT` | Service account email for WIF | `seedtest-deployer@univprepai.iam.gserviceaccount.com` |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | WIF provider full path | `projects/123.../github/providers/github-provider` |

### Usage

#### Local Execution

```bash
# Set environment variables
export GCP_PROJECT_ID=univprepai
export GKE_CLUSTER=seedtest-main
export GKE_LOCATION=asia-northeast3
export GCP_WIF_SERVICE_ACCOUNT=seedtest-deployer@univprepai.iam.gserviceaccount.com
export GCP_WORKLOAD_IDENTITY_PROVIDER=projects/.../providers/github-provider

# Run the audit
bash scripts/gcp/env_audit.sh
```

#### VS Code Task

Run from VS Code:
1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type "Tasks: Run Task"
3. Select "Env Audit (GCP)"

#### GitHub Actions

The audit runs automatically via the "Env Audit Launcher" workflow:

```bash
gh workflow run "Env Audit Launcher" --ref main
```

### Output

The script generates:
- **Console output**: Color-coded INFO/WARN/ERR messages
- **audit-summary.md**: Detailed audit results

### What It Checks

1. **Repo Variables**: All required variables are set
2. **Enabled APIs**: 
   - container.googleapis.com
   - iamcredentials.googleapis.com
   - sts.googleapis.com
   - artifactregistry.googleapis.com
   - secretmanager.googleapis.com
3. **GKE Cluster**: Accessibility via region/zone
4. **kubectl Access**: Namespace access test
5. **WIF Bindings**: Service account and principalSet configuration

### Exit Codes

- `0`: All checks passed
- `1`: One or more checks failed

### Troubleshooting

**Issue**: `GCP_PROJECT_ID missing`
- **Solution**: Set the environment variable or ensure `gcloud config get-value project` returns a value

**Issue**: `Cluster not found`
- **Solution**: Verify cluster name and location, check if using `--region` vs `--zone`

**Issue**: `WIF binding MISSING/MISMATCH`
- **Solution**: Run the WIF setup commands (see main documentation)

### Related Workflows

- `.github/workflows/env-audit.yml`: Reusable workflow
- `.github/workflows/env-audit-launcher.yml`: Launcher workflow

