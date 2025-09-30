# 🔧 Monthly Optimization Card Template

**Month:** $(date +%Y-%m)
**Owner:** @mpcstudy
**Due Date:** $(date -d "+1 month" +%Y-%m-01)

## 📊 Current Metrics (from last monthly report)
- **Availability (Frontend):** [%] (target: ≥99.9%)
- **Availability (Backend):** [%] (target: ≥99.9%)
- **P95 Latency (API):** [ms] (target: <500ms)
- **P95 Latency (Frontend):** [ms] (target: <500ms)
- **Error Rate (4xx):** [%] (target: <1%)
- **Error Rate (5xx):** [%] (target: <1%)
- **Change Failure Rate:** [%] (target: <15%)
- **MTTR:** [h] (target: <2h)
- **Lead Time:** [h] (target: <24h)
- **Review Depth:** [count] (target: 1-2)
- **CI Pass Rate:** [%] (target: ≥95%)
- **Auto-merge Rate:** [%] (target: ≥50%)
- **Critical Vulnerabilities:** [count] (target: 0)
- **High Vulnerabilities:** [count] (target: ≤3)
- **Dependency Freshness:** [%] (target: ≥80%)
- **Test Coverage (Line):** [%] (trend: ↗️)
- **Test Coverage (Branch):** [%] (trend: ↗️)

## 🎯 Top-3 Bottlenecks (Priority: Cost↓/Effect↑/Risk→)

### 1. [Primary Bottleneck]
- **Current:** [value]
- **Target:** [value]
- **Gap:** [gap]
- **Priority:** 1 (High Impact, Low Risk)

### 2. [Secondary Bottleneck]
- **Current:** [value]
- **Target:** [value]
- **Gap:** [gap]
- **Priority:** 2 (Medium Impact, Medium Risk)

### 3. [Tertiary Bottleneck]
- **Current:** [value]
- **Target:** [value]
- **Gap:** [gap]
- **Priority:** 3 (Low Impact, Low Risk)

## 🔧 Optimization Plan

### **Primary Action (This Month)**
- **Action:** [Specific action to take]
- **Expected Impact:** Δ [expected_change]
- **Implementation:** [How to implement]
- **Timeline:** [When to complete]
- **Success Metric:** [How to measure]

### **Secondary Action (Next Month)**
- **Action:** [Backup action if primary fails]
- **Expected Impact:** Δ [expected_change]
- **Implementation:** [How to implement]
- **Timeline:** [When to complete]
- **Success Metric:** [How to measure]

### **Tertiary Action (Future)**
- **Action:** [Additional optimization]
- **Expected Impact:** Δ [expected_change]
- **Implementation:** [How to implement]
- **Timeline:** [When to complete]
- **Success Metric:** [How to measure]

## 📈 Success Metrics
- **Primary Metric:** [main_metric] target: [target_value]
- **Secondary Metrics:** [additional_metrics]
- **Measurement Period:** 4 weeks
- **Validation Method:** Compare with next monthly report

## 🔄 Implementation Checklist
- [ ] **Week 1:** Implement primary action
- [ ] **Week 2:** Monitor initial results
- [ ] **Week 3:** Implement secondary action if needed
- [ ] **Week 4:** Measure and validate results
- [ ] **Next Month:** Compare with baseline metrics

## 📋 Failure Analysis (if target not met)
- [ ] **Root Cause:** [Why it didn't work]
- [ ] **Lessons Learned:** [What we learned]
- [ ] **Next Experiments:** [2-3 new ideas to try]
- [ ] **Process Improvement:** [How to improve the process]

## 🎯 Monthly Review
- [ ] **Results:** [Actual vs Expected]
- [ ] **Impact:** [Quantified improvement]
- [ ] **Next Month:** [What to optimize next]
- [ ] **Documentation:** [Update runbooks/docs]

---

## 🧰 Quick Tuning Items (Copy-Paste Ready)

### **CI Optimization**
```yaml
# Cache key with lockfile for better hit rate
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    key: ${{ runner.os }}-pnpm-${{ hashFiles('**/pnpm-lock.yaml') }}
    path: |
      ~/.pnpm-store
      node_modules
      apps/*/node_modules
      packages/*/node_modules
    restore-keys: |
      ${{ runner.os }}-pnpm-
```

### **Auto-merge Rules**
```yaml
# Dependencies + automerge for faster updates
- name: Auto-merge dependency updates
  if: |
    contains(github.event.pull_request.labels.*.name, 'area:dependencies') &&
    contains(github.event.pull_request.labels.*.name, 'automerge') &&
    github.event.pull_request.draft == false
```

### **Canary Parameters**
```yaml
# Modular canary settings for easy tuning
canary_percentage: 10    # 1-50%
canary_duration: 30      # 5-120 minutes
success_threshold: 95    # 80-99%
rollback_threshold: 80   # 70-90%
```

### **Error Budget Alerts**
```yaml
# Dual threshold alerts for staged response
warning_threshold: 50%   # Early warning
critical_threshold: 80%  # Immediate action
emergency_threshold: 95% # Stop all deployments
```

---

*This template ensures data-driven, measurable, and iterative improvements.*
