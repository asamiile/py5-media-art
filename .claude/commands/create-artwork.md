Follow the workflow in `CLAUDE.md` to autonomously create exactly one new py5 media art sketch and finish all steps end-to-end.

The workflow uses two skills:
- **Artist** (`.agents/skills/artist/SKILL.md`): designs and implements the sketch
- **Critic** (`.agents/skills/critic/SKILL.md`): reviews code and `preview.png`, scores 4 axes, and returns APPROVE or REVISE

Execution rules (strict):
1. Run one full iteration only (no infinite loop).
2. Use branch `feature/works-YYYYMMDD` (create or reuse).
3. Complete Planner/Artist/Critic flow from `CLAUDE.md`.
4. Loop Artist -> Critic up to 2 revisions; on the 3rd review, force APPROVE per critic rule.
5. Ensure preview exists before review: `sketch/{work_name}/preview.png`.
6. If skill invocation fails (for example, unknown skill), do not stop:
   - Continue with a fallback self-critique using the exact output format in `.agents/skills/critic/SKILL.md`.
   - Still produce APPROVE or REVISE explicitly.
7. Update `sketch/WORKS.md` and `sketch/FEEDBACK.md`.
8. Before commit, run a staging sanity check:
   - `git status --short`
   - stage only intended files for this work:
     - `sketch/{work_name}/`
     - `sketch/WORKS.md`
     - `sketch/FEEDBACK.md` (if changed)
9. Never delete unrelated files (for example, root `preview.png`) unless explicitly requested.
10. Commit and push. If commit fails, fix the cause, restage, and create a new commit.
11. Finish by reporting:
   - work name
   - critique verdict and score
   - files changed
   - commit hash
