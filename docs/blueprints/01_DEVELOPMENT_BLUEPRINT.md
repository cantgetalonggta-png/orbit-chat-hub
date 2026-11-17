# DEVELOPMENT BLUEPRINT
## future_session_merge v3 — Full Stack Development Protocol

**Owner**: DEP-01 ORBIT-LEAD + LC-03 TOOLCHAIN  
**Effort Target**: xhigh / effort-100  
**Status**: ACTIVE PRODUCTION  

---

## 1. DEVELOPMENT PHASES (STRICT SEQUENCE)

### Phase 0 — Environment Lock
- Confirm primary session 211e2cba-1b23-5ce8-945a-d5e158b037a2 is live.
- Confirm SessionRegistry is loaded and all 23 agents are registered.
- Confirm DEBUG-OPTS catalogue is available via DEP-05.
- Confirm all 5 public surfaces return 200.
- Confirm sandbox_selectable = on.
- Confirm Hades worker envelope is the only capability ceiling in force.

### Phase 1 — Skill & Tool Surface Hardening
- Verify session-root-lock is permanent and always-on.
- Verify master-run-command-center skill is loaded.
- Verify ai-coding-gateway-skill-set references are available (ocx, Orca patterns).
- Verify skill-distillation-system DEBUG-OPTS list is complete.
- Expand tool surface if needed: edit_file, write_file, browser_tab, browser_network_details (session_create_tool_expansion mode).

### Phase 2 — Agent Individuality & Registry Integrity
- Every agent must have unique session ID (already locked).
- Every agent must declare its callsign, team, and reporting line.
- SessionRegistry.auditAllSessions() must be callable and produce clean JSON.
- Tab unlock state must only be mutable under BuildConfig.DEBUG equivalent (sandbox debug modes).

### Phase 3 — Frontend Development Track (FE Team)
Owned by FE-01 UI-SHELL with sub-ownership:
- FE-02: Swarm roster + filters + status chips
- FE-03: KPI board + health matrix
- FE-04: Asset linking + download + static verification
- FE-05: A11Y + mobile responsive
- FE-06: Export (CSV/JSON) + clipboard + audit dump

Development rules:
- All UI state flows through SwarmViewModel → SwarmRepository.
- No direct DOM mutation of agent status; always go through registry.
- Accessibility is not optional (FE-05 gate).
- Export must include redacted secrets and individuality markers.

### Phase 4 — Backend / Bridge Development Track
- LiveKitBridge remains the sole configuration injection point.
- SessionRegistry is the sole source of truth for session specs.
- Background tasks are owned exclusively by DEP-06 TASK-DAEMON.
- Health probes are owned by DEP-02 PULSE-HEALTH.
- Deploy gates owned by DEP-03 SHIP-GATE.

### Phase 5 — Research Pipeline Development Track
- RS-01 owns public surface inventory.
- RS-02 owns citation provenance.
- RS-03 owns SOLID/MAYBE claim splitting.
- RS-04 owns report architecture.
- RS-05 owns diff/snapshot watching.
- RS-06 owns hard scope fence (public-record only).

### Phase 6 — Learning & Operator Track
- LC-01 owns first-run / onboarding.
- LC-02 owns skill library browser.
- LC-03 owns toolchain documentation.
- LC-04 owns runbooks and redeploy procedures.
- LC-05 owns tabletop drills and failure practice.

### Phase 7 — Continuous Verification Loop
- DEP-02 runs continuous surface health.
- DEP-04 mirrors artifacts and propagates status.
- DEP-06 maintains task queue and heartbeats.
- DEP-05 controls which debug modes are live.
- Any failure escalates to DEP-01 for decision.

---

## 2. REQUIRED ARTIFACTS PER PHASE

- Phase 0: session_status.json (always present)
- Phase 1: skills verification report
- Phase 2: full agent registry dump (auditAllSessions)
- Phase 3: frontend component inventory + a11y checklist
- Phase 4: bridge configuration schema + LiveKit worker status
- Phase 5: research pipeline status + scope compliance log
- Phase 6: onboarding checklist + runbook index
- Phase 7: continuous verification log (append-only)

All artifacts land under /home/workdir/artifacts/ and are mirrored by DEP-04.

---

## 3. FAILURE & RECOVERY CONTRACT

1. Soft failure → automatic retry with exponential backoff (DEP-06).
2. Health degradation → DEP-02 alerts + surface quarantine if needed.
3. Scope violation → RS-06 blocks + logs + notifies DEP-01.
4. Secrets exposure risk → immediate redaction + chain abort + DEP-01 alert.
5. Agent individuality breach → hard stop + registry lock + DEP-01 intervention.
6. "IMPOSSIBLE TO CONTINUE" is the only terminal state. It requires explicit declaration by DEP-01 after all recovery paths are exhausted.

---

## 4. EFFORT & REASONING LEVELS

Supported levels (from SessionSpec):
- low
- medium
- high
- xhigh
- effort-100

Default for production orchestration: **xhigh**.  
Critical path (registry, gates, scope): **effort-100** when available.

---

## 5. DEVELOPMENT TOOLCHAIN ALIGNMENT

- Use ai-coding-gateway patterns (ocx / Orca) for multi-agent routing and worktree isolation when expanding.
- All new skills must be installable via the skill-distillation-system path.
- No external rule merge is permitted (no_external_rule_merge mode always on).

This development blueprint is subordinate to the Master Orchestration Blueprint and cannot override hierarchy or continuity lock.
