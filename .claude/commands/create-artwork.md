Follow the workflow in `CLAUDE.md` to autonomously create exactly one new py5 media art sketch and finish all steps end-to-end.

The workflow uses two skill documents:
- **Artist** (`.agents/skills/artist/SKILL.md`): designs and implements the sketch
- **Critic** (`.agents/skills/critic/SKILL.md`): reviews code and `preview.png`, scores 4 axes, and returns APPROVE or REVISE

Execution rules (strict):
1. Run one full iteration only (no infinite loop).
2. Use branch `feature/works-YYYYMMDD` (create or reuse).
3. Complete Planner/Artist/Critic flow from `CLAUDE.md`.
4. Do not depend on skill invocation tooling. Read the skill markdown files directly and follow their instructions.
5. At start, check repository state with `git status --short`:
   - If there are unrelated pending changes, stop and report them instead of auto-committing old work.
   - Only continue when changes are clean or clearly scoped to this iteration.
6. Render discipline (to prevent preview mismatch):
   - Run render from repo root with exact path form: `uv run python sketch/{work_name}/main.py`.
   - For each revision, render exactly once, then treat that `preview.png` as authoritative for critique.
   - Do not run extra render commands after APPROVE unless explicitly requested.
   - If a rerender is required during revision, archive previous output first as `preview_v{n}.png`.
7. Ensure preview exists before review: `sketch/{work_name}/preview.png`.
8. Add quick preview validity checks before critique:
   - Verify file exists and non-trivial size (not near-empty).
   - Verify the image is not effectively blank (all-black or near-uniform).
   - If invalid, revise code and rerender before critique.
9. Critique loop:
   - Follow the critic format in `.agents/skills/critic/SKILL.md`.
   - Loop Artist -> Critic up to 2 revisions; on the 3rd review, force APPROVE per critic rule.
   - If any review step fails, continue with a fallback self-critique in the exact critic format, and still output APPROVE or REVISE explicitly.
10. Update both `sketch/WORKS.md` and `sketch/FEEDBACK.md` every iteration.
   - `FEEDBACK.md` update is mandatory (at least one concise note for the new work).
11. Before commit, run a staging sanity check:
   - `git status --short`
   - stage only intended files for this work:
     - `sketch/{work_name}/`
     - `sketch/WORKS.md`
     - `sketch/FEEDBACK.md`
12. Never delete unrelated files (for example, root `preview.png`) unless explicitly requested.
13. Commit and push. If commit fails, fix the cause, restage, and create a new commit.
14. Finish by reporting:
   - work name
   - critique verdict and score
   - files changed
   - commit hash
   - whether rerender happened (yes/no) and final preview file path
