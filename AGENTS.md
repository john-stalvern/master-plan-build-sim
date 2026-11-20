# Master Planner — project rules (all worker profiles)

## Speed directive (PM)
Maximise speed of completion by using subagents (`delegate_task`) wherever
parts of your card are independent:
- Batch independent subtasks into ONE delegate_task call (tasks=[...]) so they
  run concurrently (cap: 10 children).
- Good splits: research/reading vs drafting; writing tests vs implementing;
  build verification vs diff review; per-file or per-metric chunks.
- Children share your workspace: give each child explicit file ownership and
  the relevant docs/CONTRACT.md excerpts in its context. Children cannot see
  the kanban board or ask questions — pass everything they need.
- YOU remain responsible: integrate children's output, run final verification
  yourself, commit only your owned files, then kanban_complete with evidence.
  Never delegate the final verification/commit/complete step.

## Contract
docs/CONTRACT.md is frozen. Types, signatures, constants, and file ownership
are binding. Header changes need PM approval via a kanban comment.

## Verification
Every code card: make (zero warnings), make test green where tests exist,
./masterplanner --smoke exits 0. Evidence goes in the kanban_complete summary.
