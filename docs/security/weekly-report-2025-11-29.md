# 🔒 Weekly Security Report - 2025-11-29

**Report Period**: 2025-11-22 to 2025-11-29

---

## 📊 Summary

### Dependabot Alerts (Open)
- **Total**: 6
  - 🔴 **Critical**: 1
  - 🟠 **High**: 2
  - 🟡 **Medium**: 3
  - 🟢 **Low**: 0

### By Ecosystem
- 🐍 **Python (pip)**: 3 alerts
- 📦 **npm**: 3 alerts

---

## 🎯 Action Items

### High Priority (This Week)
1. 🟠 Update `glob` (npm) - #29
2. 🟠 Update `ecdsa` (pip) - #21
3. 🔴 Update `python-jose` (pip) - #7

### Medium Priority (Next 2 Weeks)
- Review and merge pending Dependabot PRs
- Update dependencies with medium severity issues
- Review security best practices

---

## 📈 Trends

### Week-over-Week
- Open alerts: 6 (need historical data)
- Dependabot PRs merged: (need historical data)
- New vulnerabilities discovered: (need historical data)

### Monthly Overview
- Average time to patch: (need historical data)
- Security updates applied: (need historical data)

---

## 🔗 Quick Links

- [Dependabot Dashboard](https://github.com/dreamseedai/dreamseed_monorepo/security/dependabot)
- [Security Advisories](https://github.com/dreamseedai/dreamseed_monorepo/security/advisories)
- [Vulnerability Alerts](https://github.com/dreamseedai/dreamseed_monorepo/security/dependabot)

---

## 📝 Detailed Alerts

### Open Alerts by Severity

#### Critical (🔴)
- **python-jose** (pip) - #7

#### High (🟠)
- **glob** (npm) - #29
- **ecdsa** (pip) - #21

#### Medium (🟡)
- **js-yaml** (npm) - #28
- **esbuild** (npm) - #27
- **python-jose** (pip) - #6

---

## 💡 Recommendations

1. **Immediate Actions** (Critical/High severity)
   - Review and merge Dependabot PRs for critical/high severity issues
   - Test updates in staging before production
   - Monitor application logs after updates

2. **Weekly Maintenance**
   - Review this report every Monday
   - Triage new Dependabot alerts
   - Update dependencies proactively

3. **Process Improvements**
   - Enable auto-merge for low-risk updates (patch versions)
   - Set up Slack notifications for critical alerts
   - Schedule quarterly dependency refresh

---

**Generated**: 2025-11-29T20:46:25.073219  
**Tool**: `scripts/security/weekly_report.py`
