# Assignment Template YAML Integration Guide

## Overview

The teacher dashboard now supports external configuration via `config/assignment_templates.yaml`, allowing you to customize assignment templates, permissions, IdP header mappings, and role canonicalization without modifying code.

## File Structure

```
portal_front/dashboard/
├── app_teacher.R              # Main Shiny app (now loads YAML config)
├── config/
│   └── assignment_templates.yaml  # External configuration file
├── etl_realtime.R             # Real-time ETL pipeline
├── README_teacher.md          # Usage documentation
└── IMPLEMENTATION_SUMMARY.md  # Technical implementation details
```

## Configuration Loading

### Automatic Loading

The dashboard automatically loads `config/assignment_templates.yaml` on startup:

```r
CONFIG <- load_config()
ASSIGNMENT_TEMPLATES <- CONFIG$templates %||% list()
ROLE_PERMISSIONS <- CONFIG$permissions %||% list()
```

### Fallback Behavior

If the YAML file is missing or invalid, the system falls back to hardcoded defaults:

```r
templates:
  very_low: remedial_basics
  low: supplementary_review
  mid: core_practice
  high: challenge_advanced
  very_high: enrichment_extension
```

## Customization Examples

### 1. Changing Assignment Templates

Edit `config/assignment_templates.yaml`:

```yaml
templates:
  very_low:
    template_id: "custom_remedial"
    catalog_ids:
      - "CUSTOM-R1"
      - "CUSTOM-R2"
    tags: ["remedial", "foundational"]
    difficulty: 1
    estimated_minutes: 25
```

The dashboard will automatically use `custom_remedial` instead of `remedial_basics` when the "매우낮음" CTA is clicked.

### 2. Adding IdP Integration

Configure your reverse proxy headers:

```yaml
idp_header_mappings:
  your_idp:
    user_header: "X-Custom-User"
    org_header: "X-Custom-Org"
    roles_header: "X-Custom-Roles"
    roles_separator: ","
```

Then set environment variables before running the dashboard:

```bash
export AUTH_HEADER_USER="X-Custom-User"
export AUTH_HEADER_ORG="X-Custom-Org"
export AUTH_HEADER_ROLES="X-Custom-Roles"
```

### 3. Role Canonicalization

Map your IdP's role names to standard roles:

```yaml
role_mappings:
  admin:
    - "system_admin"
    - "school_principal"
    - "head_teacher"
  teacher:
    - "class_teacher"
    - "subject_instructor"
  counselor:
    - "guidance_counselor"
    - "student_advisor"
```

The `canonicalize_roles()` function will automatically convert these to `admin`, `teacher`, `counselor`, or `viewer`.

### 4. Permission Customization

Modify role permissions:

```yaml
permissions:
  admin:
    can_assign: true
    can_view_all_classes: true
    can_modify_thresholds: true
  teacher:
    can_assign: true
    can_view_all_classes: false  # Changed: only own classes
    can_modify_thresholds: false
```

**Note:** Permission enforcement is partially implemented. Currently, only `can_assign` is actively checked in the CTA button handlers.

## Environment Variables

### Required for Production

```bash
# IdP header mapping (if not using defaults)
export AUTH_HEADER_USER="X-User"           # Default
export AUTH_HEADER_ORG="X-Org-Id"          # Default
export AUTH_HEADER_ROLES="X-Roles"         # Default
export AUTH_ROLES_SEPARATOR=","            # Default

# Assignment API endpoint
export ASSIGNMENT_API_URL="https://api.example.com/assignments"

# Risk thresholds (optional, uses config defaults)
export RISK_THETA_DELTA="0.02"
export RISK_ATTENDANCE="0.25"
export RISK_GUESS="0.15"
export RISK_OMIT="0.12"
```

### Development Mode

```bash
# Local testing without IdP
export DEV_USER="test_teacher"
export DEV_ORG_ID="org_test"
export DEV_CLASS_ID="class_101"
export ASSIGNMENT_API_URL="http://localhost:8000/api/assignments"
```

## Deployment Workflow

### 1. Update Configuration

```bash
cd /home/won/projects/dreamseed_monorepo/portal_front/dashboard
vim config/assignment_templates.yaml
```

### 2. Validate YAML Syntax

```bash
# Using R
Rscript -e "yaml::yaml.load_file('config/assignment_templates.yaml')"

# Or using Python
python3 -c "import yaml; yaml.safe_load(open('config/assignment_templates.yaml'))"
```

### 3. Restart Dashboard

```bash
# If running via systemd
sudo systemctl restart portal-teacher-dashboard

# Or if running manually
pkill -f app_teacher.R
Rscript app_teacher.R --port 8081 &
```

### 4. Verify Loading

Check the R console output for:

```
[load_config] Config file not found: config/assignment_templates.yaml. Using defaults.
```

If you see this message, the YAML file wasn't found. Otherwise, it loaded successfully.

## Code Integration Points

### 1. Template ID Retrieval

Before (hardcoded):

```r
ok <- call_assignment_api(students$student_id, "remedial_basics", claims, assignment_auth)
```

After (YAML-driven):

```r
template_id <- ASSIGNMENT_TEMPLATES$very_low$template_id %||% "remedial_basics"
ok <- call_assignment_api(students$student_id, template_id, claims, assignment_auth)
```

### 2. Permission Checks

```r
if (!(has_role(claims, "teacher") || has_role(claims, "admin"))) {
  showNotification("과제 배정 권한이 없습니다.", type = "error", duration = 4)
}
```

Future enhancement: Use `ROLE_PERMISSIONS[[role]]$can_assign` dynamically.

### 3. Role Canonicalization

```r
canonicalize_roles <- function(raw_roles) {
  # Uses hardcoded regex patterns + YAML role_mappings (future)
  if (any(grepl("admin|관리자|principal|교장", rs))) canon <- c(canon, "admin")
  # ...
}
```

## Testing

### Unit Test YAML Loading

```r
# Test valid YAML
CONFIG <- load_config("config/assignment_templates.yaml")
stopifnot(!is.null(CONFIG))
stopifnot("templates" %in% names(CONFIG))

# Test missing file
CONFIG <- load_config("config/nonexistent.yaml")
stopifnot(!is.null(CONFIG$templates))  # Should have defaults
```

### Integration Test Template Assignment

```r
# Simulate CTA click for very_low bucket
template_id <- ASSIGNMENT_TEMPLATES$very_low$template_id %||% "remedial_basics"
print(paste("Using template:", template_id))

# Expected output: "Using template: remedial_basics" (or custom value)
```

### Test Role Canonicalization

```r
# Test with custom role names
raw <- c("system_admin", "class_teacher", "unknown_role")
canon <- canonicalize_roles(raw)
print(canon)

# Expected: c("admin", "teacher", "unknown_role")
```

## Migration Path

### Phase 1: YAML for Templates Only (Current)

- ✅ Load `assignment_templates.yaml`
- ✅ Use template IDs from YAML in CTA handlers
- ✅ Fallback to hardcoded defaults if missing

### Phase 2: Dynamic Permissions (Future)

- Replace hardcoded `has_role(claims, "teacher")` checks with `ROLE_PERMISSIONS[[role]]$can_assign`
- Add UI elements to disable/hide features based on permissions

### Phase 3: Runtime Threshold Adjustment (Future)

- Load risk thresholds from YAML instead of environment variables
- Add admin UI to modify thresholds without restart

### Phase 4: Full IdP Integration (Future)

- Use `idp_header_mappings` from YAML to auto-configure header names
- Auto-generate `canonicalize_roles()` logic from `role_mappings` section

## Troubleshooting

### Issue: Templates Not Loading from YAML

**Symptoms:**
- Dashboard always uses hardcoded templates (e.g., `remedial_basics`)
- No warning about missing config file

**Solution:**
1. Check file path: `config/assignment_templates.yaml` relative to `app_teacher.R`
2. Verify YAML syntax: `yaml::yaml.load_file('config/assignment_templates.yaml')`
3. Check R console for `[load_config]` messages

### Issue: Invalid YAML Syntax

**Symptoms:**
```
Warning: [load_config] Failed to load YAML: ...
```

**Solution:**
- Validate YAML at https://www.yamllint.com/
- Common issues: incorrect indentation, missing colons, unquoted special characters

### Issue: Role Permissions Not Working

**Symptoms:**
- All users can assign, regardless of role

**Cause:**
- Permission enforcement is only partially implemented (only `can_assign` in CTA handlers)

**Workaround:**
- Use reverse proxy to block unauthorized access
- Wait for Phase 2 implementation (dynamic permission checks)

## Best Practices

1. **Version Control**: Commit `assignment_templates.yaml` to git
2. **Environment Separation**: Use different YAML files for dev/staging/prod
3. **Validation**: Run YAML syntax check in CI/CD pipeline
4. **Documentation**: Update this guide when adding new config sections
5. **Backward Compatibility**: Always provide fallback defaults in `load_config()`

## Related Documentation

- [README_teacher.md](./README_teacher.md) - Dashboard usage guide
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - Technical implementation details
- [assignment_templates.yaml](./config/assignment_templates.yaml) - Configuration file

## Future Enhancements

- [ ] Hot-reload configuration without restart (via `observeEvent` + file watcher)
- [ ] Admin UI for editing templates/permissions in-app
- [ ] Validation schema for YAML (using `jsonlite` + JSON Schema)
- [ ] Multi-language template labels (i18n support)
- [ ] A/B testing support (multiple template variants)
