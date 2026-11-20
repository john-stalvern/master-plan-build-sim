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

## Worktree protocol (binding — you AND your subagents)
Parallel work on one checkout causes collisions. Use git worktrees:

1. Subagents (delegate_task): worktree isolation is ENABLED in your profile
   (delegation.worktree_isolation=true). Each child gets its own worktree and
   branch automatically. When a child finishes, its work is archived and its
   branch is kept for you to merge. YOU must integrate: from the main checkout
   run `git merge <child-branch>` (or cherry-pick), resolve any conflict in
   YOUR owned files only, then verify (make / make test / --smoke) before
   committing. Never assume a child's edits landed in your checkout — check
   `git worktree list` and `hermes worktree list` (shows archives) and merge
   explicitly. Recover an archived child with `hermes worktree restore <name>`.
2. Give each child ONE owned file or one disjoint file set in its context,
   plus the relevant CONTRACT.md excerpts. Two children must never own the
   same file. Children cannot see the board — pass everything they need.
3. Manual worktrees (experiments, alternative approaches): create under
   .worktrees/ with `git worktree add .worktrees/<name> -b wt/<card>-<name>`.
   Work there, commit, then merge the branch into main from the main checkout
   and `git worktree remove .worktrees/<name>`. Never leave unmerged work in
   a removed tree; never edit main-checkout files from inside a worktree session.
4. Kanban cards with `--workspace worktree` already run in .worktrees/<task-id>/
   on their own branch: commit there, push the branch, then merge to main and
   push main. The dispatcher preserves these trees; clean up after merging.
5. Hygiene: `git worktree list` before and after your card. Remove only trees
   you created and have merged. Never `git worktree remove --force` a tree
   with unmerged commits. Never touch another worker's tree.
6. The main checkout stays on branch main. Do not switch its branch; do not
   check out a worktree branch in the main checkout.

## Gates (minimal by design)
- No human review gates between cards. The ONLY acceptance gate is T5 QA.
- Do not kanban_block for decisions you can make from CONTRACT.md; block only
  for genuine external blockers (missing creds, broken infra, contract conflict).
- Contract conflicts: comment on your card tagging PM, propose the fix, and
  proceed with the contract-as-written unless PM replies otherwise.
