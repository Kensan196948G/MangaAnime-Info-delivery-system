---
name: Auto Repair 7x Loop
about: Automated issue template for 7-attempt repair loops with 30-minute cooldown
title: "🔧 Auto-Repair: [WORKFLOW_NAME] Failed"
labels: auto-repair-7x, automated, error
assignees: ''

---

## 🚨 Automated Error Detection

**Failed Workflow:** <!-- WORKFLOW_NAME -->
**Failure Time:** <!-- TIMESTAMP -->
**Workflow Run:** <!-- WORKFLOW_URL -->
**Commit:** <!-- COMMIT_SHA -->

### 📊 Repair Status

- **Current Cycle:** 1
- **Attempts in Cycle:** 0 / 7
- **Total Attempts:** 0
- **Status:** 🔄 Pending Repair
- **Next Action:** Awaiting repair loop execution

### 🔄 Repair Loop Configuration

| Parameter | Value |
|-----------|-------|
| Max attempts per cycle | **7** |
| Cooldown between cycles | **30 minutes** |
| Auto-escalation after | **3 cycles** (21 attempts) |
| Max total cycles | **Unlimited** (with escalation) |

### 📝 Repair Attempt Log

| Time | Cycle | Attempt | Action | Result | Details |
|------|-------|---------|--------|--------|---------|
| <!-- TIMESTAMP --> | - | - | Error Detected | 🔴 Failed | Initial detection |

### 🔧 Repair Strategy

1. **Cycle 1 (Attempts 1-7):** Basic fixes
   - Config file validation
   - Dependency updates
   - Permission fixes
   
2. **30-minute cooldown**

3. **Cycle 2 (Attempts 8-14):** Advanced fixes
   - Workflow syntax corrections
   - Cache clearing
   - Full dependency reinstall
   
4. **30-minute cooldown**

5. **Cycle 3 (Attempts 15-21):** Deep fixes
   - Complete workflow regeneration
   - System-wide validation
   - Rollback to last known good state

6. **Escalation:** If still failing after 21 attempts

### 📈 Success Metrics

- Previous success rate: <!-- SUCCESS_RATE -->
- Average fix time: <!-- AVG_FIX_TIME -->
- Most common fix: <!-- COMMON_FIX -->

### 🚦 Automation Rules

- ✅ **Auto-close** when repair succeeds
- ⏸️ **Auto-pause** during cooldown periods
- ⚠️ **Auto-escalate** after 3 cycles
- 🔄 **Auto-retry** on transient failures

---
*This issue is managed by the Auto-Repair Loop System (7x30)*
*Do not manually close unless the issue is resolved*