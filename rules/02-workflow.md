# rules/02-workflow.md — WORKFLOW ORCHESTRATION

## SUMMARY (READ FIRST)
- Non-trivial tasks (>=3 steps or architecture decisions) start in Plan Mode.
- On problems: Investigation (log/reproduction/hypothesis) → STOP & Re-plan if needed.
- Before done: verification + Evidence. "Would a staff engineer approve this?"
- If it's a band-aid, seek elegant solution. If simple fix, avoid over-engineering.

## RULES
### R1) Plan Mode (default planning mode)
- Trigger: 3+ steps OR architecture decision OR multi-step verification.
- Plan deliverable (keep brief):
  - Goals / non-goals
  - Change scope (files/modules)
  - Step plan (checklist)
  - Verification plan
  - Risks / rollback

### R2) Investigation First, then STOP
- Investigation:
  - Failure log summary (masked)
  - Minimal reproduction (test if possible)
  - Cause hypothesis + evidence
- STOP & Re-plan conditions:
  - Cause unknown
  - Approval-required action needed
  - Essential evidence insufficient

### R3) Verification Before Done
- No done without proof of operation.
- Minimum bar:
  - Test execution (possible scope)
  - Log verification (masked)
  - Accuracy/reproducibility proof
- Self-question: "Would a staff engineer approve this?"

### R4) Elegance vs Over-engineering
- For non-trivial changes: consider "is there a more elegant approach?"
- If it's a band-aid: prefer root-cause solution.
- But: for simple, obvious fixes, skip this (no over-engineering).

### R5) Context Mode
Task strictness varies by context:
- Local/Experiment: fast feedback first. Partial testing OK (explain impact).
- Analysis/Review: no code changes = no forced build/test.
- PR/Release: strict mode. Complete standard verification + Evidence.

Default:
- Code changes → PR/Release
- No code changes → Analysis/Review

## WHY
- Plan Mode reduces omissions (verification/approval/boundaries).
- Investigation → STOP flow reduces stalls while maintaining safe confidence.

## EXAMPLES
- Feature add (3+ steps): checklist plan → small diffs → test/log Evidence summary
- Unknown cause: Investigation → if still unknown → STOP & minimal questions
