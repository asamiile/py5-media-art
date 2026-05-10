Follow `.agents/skills/create-video-artwork-lite/SKILL.md` to create exactly one new py5 media art animation (video) using the lightweight workflow.

Use this command for slow execution routes, especially Claude Code connected through an NVIDIA API proxy.

Execution rules:
1. Run one animation only.
2. Do not invoke separate Planner, Artist, or Critic agents.
3. Keep planning and review concise.
4. Use branch `feature/works-YYYYMMDD`.
5. Check `git status --short` before starting. Stop if unrelated pending changes would make a clean commit unsafe.
6. Use **Format: Animation (10-30s @ 60fps)** and ensure FFmpeg encoding.
7. Generate `sketch/{work_name}/output.mp4` and `sketch/{work_name}/{work_name}_p1.png`.
8. Perform at most one revision.
9. Update `sketch/WORKS.md` and `.agents/FEEDBACK.md`.
10. Stage only intended files for this work.
11. Commit and push.
12. Report work name, score/verdict, changed files, and commit hash.
