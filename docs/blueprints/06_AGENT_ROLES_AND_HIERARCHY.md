# COMPLETE AGENT ROLES, TASKS & HIERARCHY
## 23 Agents — future_session_merge v3

**Primary Continuity**: 211e2cba-1b23-5ce8-945a-d5e158b037a2 (DEP-01 ORBIT-LEAD)  
**All agents individuality_locked = true**

---

## DEPLOYMENT ORCHESTRATION (6)

### DEP-01 ORBIT-LEAD
- Session: 211e2cba-1b23-5ce8-945a-d5e158b037a2
- Hierarchy: Root
- Role: Continuity lead, SessionRegistry owner, final authority, effort control, terminal state declarer
- Core Tasks: Protect primary session, approve high-risk modes, accept all escalations, declare IMPOSSIBLE TO CONTINUE

### DEP-02 PULSE-HEALTH
- Session: c8d1c118-9e57-406b-b238-86cdc5363c47
- Hierarchy: Reports to DEP-01
- Role: Live health probes and /api/health matrix
- Core Tasks: Continuous surface probing, latency tracking, degradation detection, health reports for KPI board

### DEP-03 SHIP-GATE
- Session: 6fb3883a-da77-49fe-b6ba-46902e21aded
- Hierarchy: Reports to DEP-01
- Role: LIVE-DEPLOYMENT gate
- Core Tasks: Validate vercel.json / pages.yml, production freeze control, deploy authorization

### DEP-04 SYNC-BUS
- Session: c1d1e9cc-9602-4cd1-831f-5dd10df9b995
- Hierarchy: Reports to DEP-01
- Role: Background synchronization and artifact mirror
- Core Tasks: Status propagation, artifact mirroring, cross-team message bus, heartbeat aggregation support

### DEP-05 DEBUG-OPTS
- Session: 344f6cd5-1562-4727-9a66-d8593b3e7cfa
- Hierarchy: Reports to DEP-01
- Role: Full DEBUG-OPTS catalogue owner
- Core Tasks: Mode activation/deactivation, catalogue maintenance, live-testing unlocks, coordination with LC-05 drills

### DEP-06 TASK-DAEMON
- Session: 64e5eebd-41b5-43ec-a762-c40731a9f2de
- Hierarchy: Reports to DEP-01 (operationally coordinates with DEP-04)
- Role: Background task runner and crew heartbeat
- Core Tasks: Task queue, multi-part orchestration, retries, progress publishing, long-running worker ownership

---

## FRONTEND ENGINEERING (6)

### FE-01 UI-SHELL
- Session: 568d6270-a86d-460b-87d7-1535f44a1680
- Hierarchy: Reports to DEP-01 (team lead for FE)
- Role: Command-center shell, nav, panels
- Core Tasks: Root layout, theme, global state containers, error boundaries

### FE-02 SWARM-VIEW
- Session: e302f5e6-2541-490f-ae94-12467ac46bbe
- Hierarchy: Reports to FE-01
- Role: Agent roster UI
- Core Tasks: Team cards, filters, status chips, individuality indicators, expandable SessionSpec views

### FE-03 KPI-BOARD
- Session: 38e3b225-03e5-41ec-9721-460559aba2d6
- Hierarchy: Reports to FE-01
- Role: Overview KPIs and health matrix
- Core Tasks: Aggregate metrics, surface health visualization, trend chips

### FE-04 ASSET-WIRE
- Session: c921f3a6-f5b5-4b22-a0ad-bb44ec3d4cf6
- Hierarchy: Reports to FE-01
- Role: Media and static asset linking
- Core Tasks: Download buttons, asset verification, static probe coordination

### FE-05 A11Y-UX
- Session: 60ee66e8-e76a-4fde-ac4b-4bff80a8914e
- Hierarchy: Reports to FE-01
- Role: Accessibility and mobile layout
- Core Tasks: WCAG compliance, contrast, keyboard/focus, responsive design, production A11Y gate

### FE-06 EXPORT-IO
- Session: 94d1315d-bc98-4736-82e0-dbb866503f37
- Hierarchy: Reports to FE-01
- Role: Export and clipboard
- Core Tasks: CSV/JSON export of roster/KPIs/audits, clipboard helpers, redacted dump generation

---

## RESEARCH (6)

### RS-01 SCOUT-WEB
- Session: 08e87b41-196a-439e-b367-e5814927a65e
- Hierarchy: Reports to DEP-01
- Role: Public URL inventory and live surface map
- Core Tasks: Discover and maintain public surface inventory

### RS-02 SOURCE-MAP
- Session: 843b27c9-64ce-47a4-bc80-8b83e868e21b
- Hierarchy: Reports to RS-01
- Role: Citation blocks and source provenance
- Core Tasks: Provenance notes, citation generation

### RS-03 CLAIM-SPLIT
- Session: 4e27f581-8882-403b-b406-5a0f7471bb7e
- Hierarchy: Reports to RS-01 / RS-02
- Role: Fact vs allegation tagging
- Core Tasks: SOLID / MAYBE classification, evidence grading

### RS-04 REPORT-ARCH
- Session: fc8a34dc-62d7-469c-a3f6-e403c7e2cba2
- Hierarchy: Reports to RS-01
- Role: Long-form report outline and section scaffolding
- Core Tasks: Report structure generation, section templates

### RS-05 DIFF-WATCH
- Session: 2b074235-5eee-474a-8b14-16c950e85200
- Hierarchy: Reports to RS-01
- Role: Surface change detection
- Core Tasks: Snapshot comparison, change notes

### RS-06 SCOPE-GUARD
- Session: 230bc671-9039-44dd-9ac0-0162ad97cbeb
- Hierarchy: Reports to DEP-01 (hard authority on scope)
- Role: Scope fence — public-record only enforcement
- Core Tasks: Block out-of-scope requests, log violations, protect the system from scope creep

---

## LEARNING-CENTER (5)

### LC-01 ONBOARD
- Session: 36f15bb7-eb60-4502-8619-2b3e215b5090
- Hierarchy: Reports to DEP-01
- Role: Operator onboarding
- Core Tasks: First-run checklist, operator briefing, initial orientation

### LC-02 SKILL-LIB
- Session: 95ec5721-522b-4876-916d-aac775c2c77c
- Hierarchy: Reports to LC-01
- Role: Local skills.json browser and glossary
- Core Tasks: Skill discovery help, glossary maintenance

### LC-03 TOOLCHAIN
- Session: 4b79e71a-b4dd-4f24-986b-c47a51beb4b4
- Hierarchy: Reports to LC-01
- Role: Toolchain blueprint docs and architecture map
- Core Tasks: Keep architecture documentation current with the blueprints

### LC-04 RUNBOOK
- Session: 81a402f4-0f69-4434-bbe7-cc4b524087d3
- Hierarchy: Reports to LC-01 / coordinates with DEP-03
- Role: Incident and redeploy runbooks
- Core Tasks: Maintain redeploy steps, incident response playbooks

### LC-05 DRILL
- Session: c5168efe-bc35-4e40-8bd4-1ee91da2e3ad
- Hierarchy: Reports to LC-01 / coordinates with DEP-05
- Role: Tabletop drills and agent role practice
- Core Tasks: Failure scenario drills, role practice, escalation practice

---

## HIERARCHY SUMMARY

- **Root**: DEP-01 ORBIT-LEAD
- **Direct reports to DEP-01**: DEP-02, DEP-03, DEP-04, DEP-05, DEP-06, FE-01, RS-01, RS-06, LC-01
- **Team-internal reporting**: FE-02..06 → FE-01; RS-02..05 → RS-01; LC-02..05 → LC-01
- **Operational coordination**: DEP-06 ↔ DEP-04; DEP-05 ↔ LC-05; DEP-03 ↔ LC-04

No agent may issue orders that contradict DEP-01 or violate individuality, secrets, or scope rules.
