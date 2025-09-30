---
name: 🚨 Incident Report
about: Report a production incident or service outage
title: '[INCIDENT] '
labels: ['incident', 'priority:high', 'area:infra']
assignees: ['mpcstudy']

---

## 🚨 Incident Report

**Severity:** [ ] P0 (Critical) [ ] P1 (High) [ ] P2 (Medium) [ ] P3 (Low)
**Service:** [Service Name]
**Start Time:** [YYYY-MM-DD HH:MM UTC]
**Detected By:** [Person/System]
**Status:** [ ] Investigating [ ] Identified [ ] Monitoring [ ] Resolved

### 📊 Impact Assessment
- **Users Affected:** [Number/Percentage]
- **Duration:** [Time]
- **Business Impact:** [Description]
- **External Dependencies:** [List any affected external services]

### 🔍 Initial Symptoms
[Describe what was observed]

### 🛠️ Immediate Actions Taken
- [ ] Health checks performed
- [ ] Team notified
- [ ] Monitoring enabled
- [ ] Rollback initiated (if applicable)
- [ ] External communication sent

### 📋 Investigation Checklist
- [ ] Health endpoints checked
- [ ] Recent deployments reviewed
- [ ] Dependencies verified
- [ ] Resource usage checked
- [ ] Logs analyzed
- [ ] Metrics reviewed
- [ ] Database status checked

### 🎯 Root Cause Analysis
[To be filled during investigation]

### 📝 Timeline
- **[Time]** - Incident detected
- **[Time]** - Investigation started
- **[Time]** - Root cause identified
- **[Time]** - Fix implemented
- **[Time]** - Service restored

### 🚀 Resolution
[Describe the fix applied]

### 📚 Lessons Learned
**What went well:**
-

**What could be improved:**
-

### 🎯 Action Items
- [ ] Action item 1
- [ ] Action item 2
- [ ] Action item 3

### 📞 Escalation
- [ ] On-call engineer notified
- [ ] Team lead notified
- [ ] Stakeholders updated
- [ ] External communication sent

---

## 🚨 Emergency Response

### Quick Commands
```bash
# Health check
curl -f https://your.domain/__ok

# Recent deployments
gh run list --limit 5

# Rollback if needed
gh workflow run rollback.yml -f environment=production
```

### Communication Template
```
🚨 INCIDENT ALERT
Severity: [P0/P1/P2/P3]
Service: [Service Name]
Issue: #[Issue Number]
Status: Investigating
ETA: [Time]
```
