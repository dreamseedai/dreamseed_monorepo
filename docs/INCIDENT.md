# 🚨 Incident Response Playbook

## 📋 Quick Reference (10-minute response)

### 🚨 **Immediate Actions (0-5 minutes)**

1. **Assess Severity**
   ```bash
   # Check system health
   curl -f https://your.domain/__ok
   curl -f https://your.domain/health
   curl -f https://your.domain/metrics
   ```

2. **Create Incident Issue**
   - Use GitHub Issue template: `incident`
   - Assign severity: `P0` (Critical), `P1` (High), `P2` (Medium), `P3` (Low)
   - Tag: `incident`, `priority:high`, `area:infra`

3. **Notify Team**
   ```bash
   # Slack notification
   curl -X POST -H 'Content-type: application/json' \
     --data '{"text":"🚨 INCIDENT: [SEVERITY] - [BRIEF_DESCRIPTION] - Issue: #[ISSUE_NUMBER]"}' \
     $SLACK_WEBHOOK_URL
   ```

### 👥 **Incident Roles**

| Role | Responsibilities | Contact |
|------|------------------|---------|
| **Incident Commander** | Overall coordination, decision making | @mpcstudy |
| **Communications** | External updates, stakeholder notifications | @mpcstudy |
| **Technical Owner** | Root cause analysis, technical fixes | @mpcstudy |
| **Documentation** | Incident logging, post-mortem | @mpcstudy |

### 🔧 **Common Incident Scenarios**

#### **Scenario 1: Service Down (P0)**
```bash
# 1. Check health endpoints
curl -f https://your.domain/__ok || echo "Service down"

# 2. Check recent deployments
gh run list --limit 5

# 3. Immediate rollback if recent deployment
gh workflow run rollback.yml -f environment=production

# 4. Check logs
gh run view --log-failed
```

#### **Scenario 2: High Error Rate (P1)**
```bash
# 1. Check error metrics
curl -s https://your.domain/metrics | jq '.errors'

# 2. Check recent changes
git log --oneline -10

# 3. Scale up if needed
# kubectl scale deployment api --replicas=5

# 4. Enable circuit breakers
```

#### **Scenario 3: Database Issues (P1)**
```bash
# 1. Check database health
curl -s https://your.domain/health | jq '.checks.database'

# 2. Check connection pool
# kubectl exec -it db-pod -- psql -c "SELECT * FROM pg_stat_activity;"

# 3. Restart database if needed
# kubectl rollout restart deployment/database
```

#### **Scenario 4: Security Incident (P0)**
```bash
# 1. Immediate response
# - Rotate secrets
# - Block suspicious IPs
# - Enable additional logging

# 2. Notify security team
# 3. Document everything
# 4. Prepare public communication
```

### 📞 **Escalation Matrix**

| Severity | Response Time | Escalation |
|----------|---------------|------------|
| **P0 (Critical)** | 5 minutes | Immediate notification to all team members |
| **P1 (High)** | 15 minutes | Notify on-call engineer + team lead |
| **P2 (Medium)** | 1 hour | Notify team lead |
| **P3 (Low)** | 4 hours | Create issue, normal process |

### 📝 **Communication Templates**

#### **Initial Alert**
```
🚨 INCIDENT ALERT
Severity: [P0/P1/P2/P3]
Service: [Service Name]
Issue: #[Issue Number]
Status: Investigating
ETA: [Time]
```

#### **Status Update**
```
📊 INCIDENT UPDATE
Issue: #[Issue Number]
Status: [Investigating/Identified/Monitoring/Resolved]
ETA: [Updated Time]
Impact: [User Impact Description]
```

#### **Resolution**
```
✅ INCIDENT RESOLVED
Issue: #[Issue Number]
Root Cause: [Brief description]
Resolution: [What was done]
Prevention: [How to prevent recurrence]
```

### 🔍 **Investigation Checklist**

- [ ] **Health Checks**: All endpoints responding?
- [ ] **Recent Deployments**: Any changes in last 24h?
- [ ] **Dependencies**: External services healthy?
- [ ] **Resources**: CPU/Memory/Disk usage normal?
- [ ] **Logs**: Any error patterns?
- [ ] **Metrics**: Error rates, latency spikes?
- [ ] **Database**: Connections, queries, locks?
- [ ] **Network**: DNS, connectivity issues?

### 🛠️ **Recovery Actions**

#### **Quick Fixes**
```bash
# Restart services
kubectl rollout restart deployment/api
kubectl rollout restart deployment/frontend

# Scale up
kubectl scale deployment api --replicas=5

# Clear caches
kubectl exec -it cache-pod -- redis-cli FLUSHALL

# Rollback deployment
gh workflow run rollback.yml -f environment=production
```

#### **Database Recovery**
```bash
# Check database status
kubectl exec -it db-pod -- pg_isready

# Restart database
kubectl rollout restart deployment/database

# Check replication lag
kubectl exec -it db-pod -- psql -c "SELECT * FROM pg_stat_replication;"
```

### 📊 **Post-Incident Process**

#### **Immediate (Within 24h)**
- [ ] **Incident Timeline**: Document all actions taken
- [ ] **Root Cause**: Identify primary cause
- [ ] **Impact Assessment**: Users affected, duration
- [ ] **Communication**: Update stakeholders

#### **Follow-up (Within 1 week)**
- [ ] **Post-Mortem**: Detailed analysis
- [ ] **Action Items**: Prevent recurrence
- [ ] **Process Updates**: Improve playbook
- [ ] **Training**: Share lessons learned

### 📋 **Incident Issue Template**

```markdown
## 🚨 Incident Report

**Severity:** [P0/P1/P2/P3]
**Service:** [Service Name]
**Start Time:** [Timestamp]
**Detected By:** [Person/System]
**Status:** [Investigating/Identified/Monitoring/Resolved]

### 📊 Impact
- **Users Affected:** [Number/Percentage]
- **Duration:** [Time]
- **Business Impact:** [Description]

### 🔍 Timeline
- **[Time]** - Incident detected
- **[Time]** - Investigation started
- **[Time]** - Root cause identified
- **[Time]** - Fix implemented
- **[Time]** - Service restored

### 🛠️ Actions Taken
- [ ] Action 1
- [ ] Action 2
- [ ] Action 3

### 🎯 Root Cause
[Detailed explanation]

### 📝 Lessons Learned
[What went well, what didn't]

### 🚀 Action Items
- [ ] Action item 1
- [ ] Action item 2
- [ ] Action item 3
```

### 🆘 **Emergency Contacts**

| Role | Contact | Backup |
|------|---------|--------|
| **On-Call Engineer** | @mpcstudy | @mpcstudy |
| **Team Lead** | @mpcstudy | @mpcstudy |
| **Security Team** | @mpcstudy | @mpcstudy |
| **Infrastructure** | @mpcstudy | @mpcstudy |

---

## 🎯 **Success Metrics**

- **MTTR (Mean Time To Resolution)**: < 30 minutes for P0
- **MTTD (Mean Time To Detection)**: < 5 minutes
- **Incident Frequency**: < 1 per month
- **Post-Mortem Completion**: 100% within 1 week

---

*This playbook is automatically updated based on incident learnings.*
