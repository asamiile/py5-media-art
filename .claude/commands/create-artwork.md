Follow the workflow in `CLAUDE.md` to autonomously create exactly one new py5 media art sketch and finish all steps end-to-end.

Use the skill documents directly:
- **Artist** (`.agents/skills/artist/SKILL.md`)
- **Critic** (`.agents/skills/critic/SKILL.md`)

Execution rules:
1. Run one artwork only.
2. Use branch `feature/works-YYYYMMDD`.
3. Check `git status --short` before starting. Stop if unrelated pending changes exist.
4. Follow the full Planner -> Artist -> Critic workflow from `CLAUDE.md`.
5. Loop Artist -> Critic up to 2 revisions until APPROVE.
6. Ensure `sketch/{work_name}/preview.png` exists before final review.
7. Update `sketch/WORKS.md` and `sketch/FEEDBACK.md`.
8. Stage only intended files for this work.
9. Commit and push.
10. Report work name, critique verdict/score, changed files, and commit hash.
