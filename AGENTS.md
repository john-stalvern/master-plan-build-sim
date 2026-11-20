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

## Git discipline (binding)
- Remote: origin = https://github.com/john-stalvern/master-plan-build-sim (private).
- After EVERY commit: `git push origin main`. If push is rejected (non-fast-forward),
  `git pull --rebase origin main` then push again. Never force-push.
- `git add` ONLY files you own per docs/CONTRACT.md. Never commit build artifacts
  (.gitignore covers *.o, masterplanner, plan.bin). Never `git add -A` blindly.
- Commit messages: "<card-id> <short summary>" e.g. "T2 sim: growth gates + tests".
- Do not rewrite history, do not touch other workers' uncommitted files.

## Gates (minimal by design)
- No human review gates between cards. The ONLY acceptance gate is T5 QA.
- Do not kanban_block for decisions you can make from CONTRACT.md; block only
  for genuine external blockers (missing creds, broken infra, contract conflict).
- Contract conflicts: comment on your card tagging PM, propose the fix, and
  proceed with the contract-as-written unless PM replies otherwise.
