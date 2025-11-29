# Teacher Dashboard Enhancements v2.0

## Overview

This document describes the four major enhancements added to the teacher dashboard after the initial implementation (v1.0). These features significantly improve teacher workflow efficiency and data visibility.

**Implementation Date**: November 6, 2025  
**Features**: 4 new enhancements  
**Files Modified**: `app_teacher.R`, `config/assignment_templates.yaml`

---

## Enhancement 1: Individual Student Assignment Action Buttons

### Purpose
Enable teachers to assign homework to individual students directly from the student table without using bucket-level batch actions.

### Implementation Details

#### UI Changes
- **Student Table**: Added "action" column with "과제 배정" (Assign) button for each student
- **Button Attributes**: Each button carries `data-student-id` and `data-theta-bucket` for context

#### Backend Changes

**New Fields in `students_tbl` Reactive**:
```r
theta_bucket = case_when(
  theta <= -1.5 ~ "very_low",
  theta > -1.5 & theta <= -0.5 ~ "low",
  theta > -0.5 & theta <= 0.5 ~ "mid",
  theta > 0.5 & theta <= 1.5 ~ "high",
  theta > 1.5 ~ "very_high",
  TRUE ~ "mid"
)
```

**JavaScript Event Handler**:
```javascript
$(document).on('click', '.assign-btn', function() {
  var studentId = $(this).data('student-id');
  var thetaBucket = $(this).data('theta-bucket');
  Shiny.setInputValue('assign_single_student', {
    student_id: studentId, 
    theta_bucket: thetaBucket, 
    timestamp: Date.now()
  }, {priority: 'event'});
});
```

**Server Event Handler**:
```r
observeEvent(input$assign_single_student, {
  # Extract student_id and theta_bucket from input
  # Validate teacher/admin role
  # Get appropriate template from ASSIGNMENT_TEMPLATES
  # Call assignment API for single student
  # Show success/failure notification with student name
})
```

### Usage

1. Browse student table to identify target student
2. Click "과제 배정" button in the action column
3. System automatically selects appropriate template based on student's θ bucket
4. Notification shows assignment result

### Benefits

- **Precision**: Assign to specific students without filtering
- **Speed**: One-click assignment from table view
- **Context-aware**: Template automatically matched to student ability level
- **Feedback**: Clear notification with student name and template

---

## Enhancement 2: Day-of-Week Attendance Variance Analysis

### Purpose
Identify students with irregular attendance patterns by analyzing absence/tardy variance across different days of the week.

### Implementation Details

#### Data Calculation

**New Metrics in `attn_metrics_tbl`**:
```r
# Day-of-week variance analysis
dow_variance <- adf %>% mutate(
  is_abs = status == "absent",
  is_tardy = status == "tardy",
  weekday = lubridate::wday(date, label = TRUE, abbr = TRUE, week_start = 1)
) %>% group_by(student_id, weekday) %>% summarise(
  abs_rate_dow = mean(is_abs),
  tardy_rate_dow = mean(is_tardy),
  .groups = 'drop'
) %>% group_by(student_id) %>% summarise(
  abs_rate_variance = var(abs_rate_dow, na.rm = TRUE),
  tardy_rate_variance = var(tardy_rate_dow, na.rm = TRUE),
  worst_day = weekday[which.max(abs_rate_dow)],
  worst_day_abs_rate = max(abs_rate_dow, na.rm = TRUE),
  .groups = 'drop'
)
```

**New Columns in Student Table**:
- `abs_variance`: Variance of absence rate across weekdays
- `worst_day`: Day with highest absence rate (e.g., "Mon", "Fri")

#### Algorithm

1. Group attendance data by `student_id` and `weekday`
2. Calculate average absence/tardy rate per weekday
3. Compute variance across all weekdays for each student
4. Identify worst_day (highest absence rate)
5. Join with overall attendance metrics

### Usage

**Interpreting Variance Values**:
- **Low variance (< 0.01)**: Consistent attendance pattern
- **Medium variance (0.01 - 0.05)**: Some day-specific issues
- **High variance (> 0.05)**: Highly irregular pattern (e.g., every Friday absent)

**Example Use Case**:
Student with:
- `abs_variance = 0.08`
- `worst_day = "Fri"`
- `worst_day_abs_rate = 0.40` (40%)

→ Indicates student misses 40% of Fridays, suggesting potential family travel pattern or extracurricular conflict.

### Benefits

- **Pattern Detection**: Identify students who skip specific days (e.g., Monday/Friday absences)
- **Intervention Planning**: Schedule important lessons on days with better attendance
- **Root Cause Analysis**: Variance + worst_day helps diagnose reasons (sports, family, etc.)
- **Early Warning**: High variance signals need for parent conference

---

## Enhancement 3: Response Pattern Anomaly Quick-Access Modals

### Purpose
Provide instant access to filtered student lists for each response anomaly pattern, enabling rapid intervention decisions.

### Implementation Details

#### UI Changes

**New Action Buttons** (below ValueBoxes):
```r
column(3, actionButton("show_pure_guess_modal", "Pure Guessing 학생 보기", ...))
column(3, actionButton("show_strategic_omit_modal", "Strategic Omit 학생 보기", ...))
column(3, actionButton("show_rapid_fire_modal", "Rapid-Fire 학생 보기", ...))
column(3, actionButton("show_multi_pattern_modal", "복합 패턴 학생 보기", ...))
```

#### Modal Event Handlers

**Pure Guessing Modal**:
```r
observeEvent(input$show_pure_guess_modal, {
  anomaly_students <- rsp %>%
    filter(guess_like_rate > RISK_GUESS_THRESHOLD & omit_rate < 0.05) %>%
    left_join(students, by = "student_id") %>%
    select(student_id, student_name, guess_like_rate, omit_rate, rapid_fire_rate, avg_response_time) %>%
    arrange(desc(guess_like_rate))
  
  showModal(modalDialog(
    size = "l",
    title = sprintf("Pure Guessing 패턴 학생 목록 (%d명)", nrow(anomaly_students)),
    renderDT({ datatable(anomaly_students, ...) })
  ))
})
```

**Similar Handlers for**:
- Strategic Omit: `omit_rate > RISK_OMIT_THRESHOLD & guess_like_rate < 0.05`
- Rapid-Fire: `rapid_fire_rate > 0.10 & avg_response_time < 20`
- Multi-pattern: All three conditions combined

### Usage

1. Expand "문항 반응 이상 패턴 세부 분석" box
2. Click pattern-specific button (e.g., "Pure Guessing 학생 보기")
3. Modal displays sortable table with:
   - Student ID and name
   - All response metrics (guess_rate, omit_rate, rapid_fire_rate, avg_response_time)
4. Sort by any column to identify worst offenders
5. Use student IDs for further investigation or intervention

### Benefits

- **Instant Access**: One-click to filtered student list (no manual filtering)
- **Complete Context**: See all response metrics in one table
- **Sortable**: Rank students by severity within pattern
- **Focused Intervention**: Bulk-select students for targeted remediation
- **Pattern Comparison**: Quickly switch between modals to compare patterns

---

## Enhancement 4: YAML Hot-Reload (Configuration Live Update)

### Purpose
Eliminate dashboard restarts when modifying assignment templates, permissions, or IdP configurations by automatically detecting and reloading config file changes.

### Implementation Details

#### Enhanced `load_config` Function

**File Modification Tracking**:
```r
load_config <- function(config_path = "config/assignment_templates.yaml") {
  # ... existing load logic ...
  config$`_last_modified` <- file.info(config_path)$mtime  # Track file timestamp
  message("[load_config] Successfully loaded config from: ", config_path)
  config
}
```

#### Change Detection Function

```r
check_config_reload <- function(config_path = "config/assignment_templates.yaml") {
  if (!file.exists(config_path)) return(FALSE)
  
  current_mtime <- file.info(config_path)$mtime
  last_mtime <- CONFIG$`_last_modified`
  
  if (is.null(last_mtime) || current_mtime > last_mtime) {
    return(TRUE)  # File changed
  }
  return(FALSE)
}
```

#### Server Hot-Reload Logic

**30-Second Timer with Auto-Reload**:
```r
server <- function(input, output, session) {
  # ... existing setup ...
  
  config_reload_timer <- reactiveTimer(30000)  # 30 seconds
  
  observe({
    config_reload_timer()  # Trigger every 30s
    
    if (check_config_reload()) {
      message("[hot-reload] Config file changed, reloading...")
      new_config <- load_config()
      
      if (!is.null(new_config)) {
        CONFIG <<- new_config
        ASSIGNMENT_TEMPLATES <<- new_config$templates %||% list()
        ROLE_PERMISSIONS <<- new_config$permissions %||% list()
        
        showNotification(
          "⚡ 설정 파일이 업데이트되었습니다 (템플릿/권한 재로드 완료)",
          type = "message",
          duration = 5,
          id = "config_reload_notification"
        )
      }
    }
  })
}
```

### Usage

#### Developer Workflow

**Before** (v1.0):
```bash
# Edit config
vim config/assignment_templates.yaml

# Restart dashboard (30s+ downtime)
sudo systemctl restart portal-teacher-dashboard
```

**After** (v2.0):
```bash
# Edit config
vim config/assignment_templates.yaml

# Wait up to 30 seconds - automatic reload with notification
# No restart needed, zero downtime
```

#### Configuration Updates

**Example 1: Change Template**
```yaml
templates:
  very_low:
    template_id: "new_remedial_v2"  # Changed from remedial_basics
```
Within 30 seconds:
- Next CTA click uses `new_remedial_v2`
- Notification confirms reload
- No user sessions interrupted

**Example 2: Update Permissions**
```yaml
permissions:
  teacher:
    can_view_all_classes: true  # Changed from false
```
Takes effect on next reactive evaluation.

### Technical Details

**Timer Interval**: 30 seconds (configurable via `reactiveTimer(30000)`)  
**Scope**: Global reassignment using `<<-` operator  
**Notification ID**: `config_reload_notification` (prevents duplicates)  
**File Check**: Uses `file.info()$mtime` for OS-level timestamp comparison

### Benefits

- **Zero Downtime**: No dashboard restart required
- **Instant Feedback**: Notification confirms successful reload
- **Safe Updates**: Invalid YAML detected without crashing dashboard
- **Multi-User Safe**: All connected sessions get updated templates simultaneously
- **DevOps Friendly**: CI/CD can update config without service interruption

### Limitations

1. **30-Second Delay**: Changes take up to 30s to apply (timer interval)
2. **No Partial Reload**: Entire config reloaded (not individual sections)
3. **No History**: Previous config not backed up automatically
4. **Manual Validation**: YAML syntax errors require manual fix

### Future Enhancements

- [ ] File system watcher (inotify) for instant reload
- [ ] Admin UI button for manual reload trigger
- [ ] Config version history with rollback
- [ ] Validation before reload (YAML schema check)
- [ ] Per-user config overrides

---

## Testing Checklist

### Enhancement 1: Individual Assignment
- [ ] Click assignment button for student with θ = -2.0 (very_low bucket)
- [ ] Verify API called with correct `template_id` from YAML
- [ ] Check notification shows student name and template
- [ ] Test with teacher role (should succeed) and viewer role (should fail)
- [ ] Verify assignment logged to API

### Enhancement 2: Day-of-Week Variance
- [ ] Create test student with absences only on Fridays
- [ ] Verify `abs_variance > 0.05` in student table
- [ ] Check `worst_day = "Fri"` appears correctly
- [ ] Compare with student having uniform attendance (variance ~0)
- [ ] Test with dataset spanning < 1 week (should handle gracefully)

### Enhancement 3: Anomaly Modals
- [ ] Click "Pure Guessing 학생 보기" with N students matching criteria
- [ ] Verify modal shows N students sorted by `guess_like_rate`
- [ ] Test with 0 matching students (should show "해당 패턴의 학생이 없습니다")
- [ ] Sort table by different columns
- [ ] Close and reopen modal (should re-query data)

### Enhancement 4: Hot-Reload
- [ ] Edit `config/assignment_templates.yaml` while dashboard running
- [ ] Change `very_low.template_id` to "test_template"
- [ ] Wait 30 seconds for reload notification
- [ ] Click "매우낮음" CTA and verify API receives "test_template"
- [ ] Test with invalid YAML (should show warning, not crash)
- [ ] Restore valid config and verify recovery

---

## Performance Considerations

### Database Impact

**Enhancement 1**: Minimal (single student query vs batch)  
**Enhancement 2**: +20% compute on `attn_metrics_tbl` (variance calculation)  
**Enhancement 3**: On-demand query (only when modal opened)  
**Enhancement 4**: File I/O every 30s (negligible)

### Optimization Opportunities

1. **Cache DOW Variance**: Calculate once per session, not per reactive update
2. **Lazy Modal Loading**: Render DT only when modal shown (currently pre-rendered)
3. **Debounce Config Check**: Skip check if no user activity in last 30s
4. **Memoize Templates**: Cache template lookups to avoid repeated list access

---

## Migration from v1.0 to v2.0

### Breaking Changes
None. All enhancements are backward-compatible additions.

### New Dependencies
- `lubridate::wday()` for weekday extraction (already in dependencies)

### Configuration Changes
- `config/assignment_templates.yaml` now supports `_last_modified` metadata key (auto-generated)

### Deployment Steps

1. **Backup Current Config**:
   ```bash
   cp config/assignment_templates.yaml config/assignment_templates.yaml.bak
   ```

2. **Update Dashboard Code**:
   ```bash
   git pull origin staging/attempt-view-lock-v1
   ```

3. **Restart Dashboard** (first time only):
   ```bash
   sudo systemctl restart portal-teacher-dashboard
   ```

4. **Verify Hot-Reload**:
   ```bash
   # Edit config
   echo "# Test change" >> config/assignment_templates.yaml
   # Watch dashboard logs for reload message
   journalctl -u portal-teacher-dashboard -f
   ```

5. **Test Each Enhancement** (use checklist above)

---

## Troubleshooting

### Issue: Assignment Button Not Working

**Symptoms**: Clicking "과제 배정" does nothing  
**Diagnosis**:
1. Check browser console for JavaScript errors
2. Verify `assign-btn` class applied: `$('.assign-btn').length` in console
3. Check server logs for `assign_single_student` event

**Fix**: Clear browser cache, hard reload (Ctrl+Shift+R)

### Issue: Day-of-Week Variance Shows NA

**Symptoms**: `abs_variance` column shows `NA` for all students  
**Diagnosis**:
1. Check if attendance data spans multiple weekdays
2. Verify `lubridate` library loaded: `library(lubridate)`

**Fix**: Ensure data covers at least 2 different weekdays per student

### Issue: Modal Shows Empty Table

**Symptoms**: Modal opens but says "해당 패턴의 학생이 없습니다"  
**Diagnosis**:
1. Verify ValueBox shows > 0 students with pattern
2. Check threshold values: `RISK_GUESS_THRESHOLD`, etc.
3. Inspect `resp_ds()` data in R console

**Fix**: If thresholds too strict, adjust via environment variables

### Issue: Hot-Reload Not Triggering

**Symptoms**: Config changes not reflected after 30+ seconds  
**Diagnosis**:
1. Check server logs for `[hot-reload]` messages
2. Verify file permissions: `ls -l config/assignment_templates.yaml`
3. Test `file.info("config/assignment_templates.yaml")$mtime` in R console

**Fix**:
```bash
# Ensure file writable
chmod 644 config/assignment_templates.yaml

# Manual reload (if needed)
touch config/assignment_templates.yaml
```

---

## Related Documentation

- [README_teacher.md](./README_teacher.md) - Dashboard usage guide
- [IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md) - v1.0 technical details
- [INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md) - YAML configuration guide
- [config/assignment_templates.yaml](./config/assignment_templates.yaml) - Configuration file

---

## Changelog

### v2.0 (2025-11-06)
- ✅ Enhancement 1: Individual student assignment action buttons
- ✅ Enhancement 2: Day-of-week attendance variance analysis
- ✅ Enhancement 3: Response pattern anomaly quick-access modals
- ✅ Enhancement 4: YAML hot-reload (zero-downtime config updates)

### v1.0 (2025-11-05)
- Initial implementation with bucket CTAs, filtering, anomaly analysis, real-time ETL
- YAML configuration file support
- IdP-agnostic authentication
- Role canonicalization

---

## Future Roadmap

### Short-term (Next Sprint)
- [ ] Add bulk assignment action in anomaly modals
- [ ] Export anomaly student lists to CSV
- [ ] Attendance variance threshold alerts
- [ ] Config reload via admin UI button (instant, no 30s wait)

### Medium-term
- [ ] Individual student historical trend charts in drilldown modal
- [ ] Predictive alerts: "Student likely to miss Friday based on pattern"
- [ ] Assignment template A/B testing support
- [ ] WebSocket-based config reload (real-time)

### Long-term
- [ ] ML-based anomaly detection (beyond threshold rules)
- [ ] Multi-class batch operations (assign to students across classes)
- [ ] Mobile-responsive UI for on-the-go interventions
- [ ] Integration with LMS for automated assignment delivery

---

**Document Version**: 2.0  
**Last Updated**: 2025-11-06  
**Maintainer**: DreamseedAI Engineering Team
