---
name: 🔧 Micro Optimization
about: Data-driven micro optimization based on monthly metrics
title: '[OPTIMIZE] '
labels: ['area:maintenance', 'type:optimization', 'priority:medium']
assignees: ['mpcstudy']

---

## 🔧 Micro Optimization Card

**Optimization Target:** [Metric to improve]
**Owner:** @mpcstudy
**Due Date:** [YYYY-MM-DD]
**Target Metric:** [metric_name]

### 📊 Current State
- **Current Value:** [current_metric_value]
- **Target Value:** [target_metric_value]
- **Gap:** [gap_analysis]
- **Priority:** [1-3 based on cost↓/effect↑/risk→]

### 🎯 Optimization Plan

#### **Primary Action (1st Priority)**
- **Action:** [Specific action to take]
- **Expected Impact:** Δ [expected_change]
- **Implementation:** [How to implement]
- **Timeline:** [When to complete]

#### **Secondary Action (2nd Priority)**
- **Action:** [Backup action if primary fails]
- **Expected Impact:** Δ [expected_change]
- **Implementation:** [How to implement]
- **Timeline:** [When to complete]

#### **Tertiary Action (3rd Priority)**
- **Action:** [Additional optimization]
- **Expected Impact:** Δ [expected_change]
- **Implementation:** [How to implement]
- **Timeline:** [When to complete]

### 📈 Success Metrics
- **Primary Metric:** [main_metric] target: [target_value]
- **Secondary Metrics:** [additional_metrics]
- **Measurement Period:** [how_long_to_measure]
- **Validation Method:** [how_to_validate]

### 🔄 Implementation Checklist
- [ ] **Week 1:** Implement primary action
- [ ] **Week 2:** Monitor initial results
- [ ] **Week 3:** Implement secondary action if needed
- [ ] **Week 4:** Measure and validate results
- [ ] **Next Month:** Compare with baseline metrics

### 📋 Failure Analysis (if target not met)
- [ ] **Root Cause:** [Why it didn't work]
- [ ] **Lessons Learned:** [What we learned]
- [ ] **Next Experiments:** [2-3 new ideas to try]
- [ ] **Process Improvement:** [How to improve the process]

### 🎯 Monthly Review
- [ ] **Results:** [Actual vs Expected]
- [ ] **Impact:** [Quantified improvement]
- [ ] **Next Month:** [What to optimize next]
- [ ] **Documentation:** [Update runbooks/docs]

---

## 📊 Quick Reference Metrics

### 🛡️ **Reliability Metrics**
- **Availability:** ≥99.9% (Frontend/Backend)
- **P95 Latency:** <500ms (API/Frontend)
- **Error Rate:** <1% (4xx/5xx)
- **Change Failure Rate:** <15%
- **MTTR:** <2h

### ⚡ **Velocity Metrics**
- **Lead Time:** <24h (PR open→merge)
- **Review Depth:** 1-2 reviewers
- **CI Pass Rate:** ≥95%
- **Auto-merge Rate:** ≥50%

### 🔒 **Quality/Security Metrics**
- **Critical Vulnerabilities:** 0
- **High Vulnerabilities:** ≤3
- **Dependency Freshness:** ≥80%
- **Test Coverage:** ↗️ (upward trend)

---

## 🧰 Quick Tuning Items (Copy-Paste Ready)

### **CI Optimization**
```yaml
# Cache key with lockfile
- name: Cache dependencies
  uses: actions/cache@v4
  with:
    key: ${{ runner.os }}-pnpm-${{ hashFiles('**/pnpm-lock.yaml') }}
    path: |
      ~/.pnpm-store
      node_modules
```

### **Auto-merge Rules**
```yaml
# Dependencies + automerge
- name: Auto-merge dependency updates
  if: contains(github.event.pull_request.labels.*.name, 'area:dependencies') && contains(github.event.pull_request.labels.*.name, 'automerge')
```

### **Canary Parameters**
```yaml
# Modular canary settings
canary_percentage: 10  # 1-50%
canary_duration: 30    # 5-120 minutes
success_threshold: 95  # 80-99%
```

### **Error Budget Alerts**
```yaml
# Dual threshold alerts
warning_threshold: 50%   # Early warning
critical_threshold: 80%  # Immediate action
```

---

*This template ensures data-driven, measurable, and iterative improvements.*
