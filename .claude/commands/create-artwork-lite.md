Follow `.agents/skills/create-artwork-lite/SKILL.md` to create exactly one new py5 media art sketch using the lightweight workflow.

Use this command for slow execution routes, especially Claude Code connected through an NVIDIA API proxy.

Execution rules:
1. Run one artwork only.
2. Do not invoke separate Planner, Artist, or Critic agents.
3. Keep planning and review concise.
4. Use branch `feature/works-YYYYMMDD`.
5. Check `git status --short` before starting. Stop if unrelated pending changes would make a clean commit unsafe.
6. Generate `sketch/{work_name}/preview.png`.
7. Perform at most one revision.
8. Update `sketch/WORKS.md` and `sketch/FEEDBACK.md`.
9. Stage only intended files for this work.
10. Commit and push.
11. Report work name, score/verdict, changed files, and commit hash.
