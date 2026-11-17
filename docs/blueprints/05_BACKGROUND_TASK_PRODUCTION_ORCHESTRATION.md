# BACKGROUND TASK MULTI-PART LONG TIRESOME PRODUCTION ORCHESTRATION
## DEP-06 TASK-DAEMON + Full Swarm Support

**Owner**: DEP-06 TASK-DAEMON  
**Oversight**: DEP-04 SYNC-BUS + DEP-01 ORBIT-LEAD  
**Goal**: Exhaust every troubleshooting, debug, testing, and recovery path until the only remaining state is "IMPOSSIBLE TO CONTINUE".

---

## 1. ORCHESTRATION PHILOSOPHY

We do not stop because something is hard, slow, or boring.  
We stop only when the system itself declares that further progress is impossible inside the current capability ceiling, security rules, and scope fence.

Every production run is multi-part.  
Every part has success criteria, failure modes, retry policy, and an explicit hand-off to the next part or to escalation.

---

## 2. STANDARD MULTI-PART TASK TEMPLATE

```
TASK_ID: <uuid or sequential>
OWNER: DEP-06 (or delegated agent)
REQUESTOR: <agent or human>
TITLE: <short>
PARTS: N
CURRENT_PART: k
MAX_RUNTIME_PER_PART: <duration or unlimited>
SUCCESS_CRITERIA: <measurable>
FAILURE_POLICY: retry ×5 with backoff → escalate
SCOPE: public-record only
SECRETS: redacted
INDIVIDUALITY: locked
```

Progress is published every 30–60 seconds on a LiveKit topic (or equivalent status channel).

---

## 3. FULL PRODUCTION RUN SEQUENCE (EXHAUSTIVE)

### PART 0 — Pre-Flight Lock
- Confirm primary session live.
- Confirm all 23 agents registered and individuality locked.
- Confirm 5 surfaces HTTP 200.
- Confirm SessionRegistry healthy.
- Confirm DEBUG-OPTS available.
- Confirm Hades envelope active.
- Output: preflight_ok.json
- Gate: If any check fails → escalate to DEP-01 immediately. Do not proceed.

### PART 1 — Health Baseline
- DEP-02 runs full surface + internal health matrix.
- Capture timestamps, latency, status codes.
- Output: health_baseline_<ts>.json
- Continue only if baseline is acceptable or degraded-but-workable.

### PART 2 — Registry Deep Audit
- Call auditAllSessions().
- Verify every agent has correct session ID, callsign, team.
- Check for duplicate session IDs or missing agents.
- Output: registry_audit_<ts>.json
- Any anomaly → DEP-01.

### PART 3 — Skill & Tool Surface Verification
- Confirm session-root-lock, master-run-command-center, ai-coding-gateway-skill-set, skill-distillation-system are loadable.
- Confirm DEBUG-OPTS catalogue matches the expected 19 items.
- Test session_create_tool_expansion availability (edit_file, write_file, browser_tab, browser_network_details) if mode is active.
- Output: skill_surface_report_<ts>.json

### PART 4 — Frontend Integrity Pass
- FE-01 / FE-02 / FE-03 / FE-05 coordinate a full UI consistency check against live registry data.
- A11Y spot checks.
- Export path dry-run (FE-06).
- Output: frontend_integrity_<ts>.json

### PART 5 — Research Pipeline Dry Run
- RS-01 maps current public surfaces.
- RS-06 confirms scope fence is closed.
- RS-03 / RS-02 perform a sample claim split + provenance on a known public fact.
- Output: research_pipeline_dryrun_<ts>.json

### PART 6 — Background Task Stress Pattern
- DEP-06 launches a controlled long-running background task (e.g., continuous health sampling or artifact generation loop).
- Runs for a defined window or until manual stop.
- Heartbeats every 60s.
- Publishes progress.
- Tests recovery from injected soft failures if DEBUG modes allow.
- Output: background_stress_log_<ts>.json

### PART 7 — Deploy Gate Simulation
- DEP-03 runs SHIP-GATE checks against current vercel/pages configuration (dry-run).
- No actual production deploy unless LIVE-DEPLOYMENT mode is explicitly authorized by DEP-01.
- Output: ship_gate_simulation_<ts>.json

### PART 8 — Cross-Team Escalation Drill
- LC-05 + DEP-05 run a tabletop drill that forces an escalation through the matrix.
- Verify that DEP-01 receives the escalation and can respond.
- Output: escalation_drill_<ts>.json

### PART 9 — Full System Snapshot & Mirror
- DEP-04 performs complete artifact mirror.
- All blueprints, logs, audits, health reports are snapshotted.
- Output: full_system_snapshot_<ts>/ directory

### PART 10 — Exhaustive Troubleshooting Loop
This is the long, tiresome part. Repeat until no new failure modes appear or recovery is impossible:

1. Inject or observe a failure (surface flake, task timeout, registry inconsistency, scope edge case, etc.).
2. Apply automatic recovery (retry, re-probe, re-sync).
3. If recovery fails → escalate one level.
4. Document the failure mode, root cause (if found), and recovery action.
5. Update runbooks (LC-04) and drills (LC-05).
6. Loop.

Continue this loop across all known failure classes:
- Network / surface unavailability
- Registry desync
- Agent individuality conflict (should be impossible, but test)
- Secrets redaction edge cases
- Scope fence edge cases
- Long-running task starvation
- Heartbeat loss
- Effort level misconfiguration
- Tool expansion mode misbehavior
- Frontend state drift
- Export corruption
- Onboarding path breakage

### PART 11 — Final Exhaustion Check
- Review all logs from PART 10.
- Confirm every recoverable path has been exercised.
- Confirm no open recoverable failures remain.
- If any recoverable path still exists → return to PART 10.
- If none remain → prepare terminal declaration package.

### PART 12 — Terminal Declaration (Only by DEP-01)
- DEP-01 reviews the exhaustion package.
- If truly exhausted → declare "IMPOSSIBLE TO CONTINUE".
- Write final_audit_and_terminal_state.json.
- Signal all background tasks to stop.
- Freeze new task acceptance.
- System enters controlled idle.

---

## 4. HEARTBEAT & PROGRESS CONTRACT

Every background part must:
- Emit a heartbeat at least every 60 seconds.
- Include: task_id, part, progress %, last_action, next_action, health_ok.
- On missed heartbeats (3 consecutive) → DEP-04 marks the task degraded and notifies DEP-01 / DEP-06.

---

## 5. ARTIFACT REQUIREMENTS

All parts write to /home/workdir/artifacts/orchestration/ with clear naming:
- <part>_<description>_<timestamp>.json
- or directories for multi-file snapshots.

DEP-04 is responsible for mirroring and retention.

---

## 6. STOP CONDITIONS

The only clean stop conditions are:
1. Explicit human / DEP-01 "finish" or "complete" for a given task.
2. Successful completion of all defined parts.
3. Declaration of "IMPOSSIBLE TO CONTINUE" by DEP-01 after full exhaustion.

Soft failures, timeouts, and degraded states are not stop conditions; they are inputs to the troubleshooting loop.

---

This orchestration blueprint is the operational heart of long-running production work. It is subordinate to the Master Orchestration Blueprint and the Supervisor Blueprint.
