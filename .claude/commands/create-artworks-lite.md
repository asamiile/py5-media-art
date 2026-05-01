Follow `.agents/skills/create-artworks-lite/SKILL.md` to continuously create py5 media art sketches using the lightweight workflow.

Use this command for slow execution routes, especially Claude Code connected through an NVIDIA API proxy.

Execution rules:
1. Repeat lightweight artwork creation until interrupted.
2. Complete exactly one artwork per iteration.
3. Do not invoke separate Planner, Artist, or Critic agents.
4. Keep planning and review concise.
5. Use branch `feature/works-YYYYMMDD`.
6. Check `git status --short` before each iteration. Stop if unrelated pending changes would make a clean commit unsafe.
7. Generate `sketch/{work_name}/preview.png` for each work.
8. Perform at most one revision per work.
9. Update `sketch/WORKS.md` and `sketch/FEEDBACK.md` every iteration.
10. Stage only intended files for the current work.
11. Commit and push each work before starting the next.
12. Stop on preview, commit, or push failure after one repair attempt.
13. After each iteration, report work name, score/verdict, changed files, and commit hash.
