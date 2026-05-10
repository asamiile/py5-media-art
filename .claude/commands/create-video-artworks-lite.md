Follow `.agents/skills/create-video-artworks-lite/SKILL.md` to continuously create py5 media art animations (videos) using the lightweight workflow.

Use this command for slow execution routes, especially Claude Code connected through an NVIDIA API proxy.

Execution rules:
1. Repeat lightweight animation creation until interrupted.
2. Complete exactly one animation per iteration.
3. Do not invoke separate Planner, Artist, or Critic agents.
4. Keep planning and review concise.
5. Use branch `feature/works-YYYYMMDD`.
6. Check `git status --short` before each iteration. Stop if unrelated pending changes would make a clean commit unsafe.
7. Use **Format: Animation (10-30s @ 60fps)** for every iteration and ensure FFmpeg encoding.
8. Generate `sketch/{work_name}/output.mp4` and `sketch/{work_name}/{work_name}_p1.png` for each work.
9. Perform at most one revision per work.
10. Update `sketch/WORKS.md` and `.agents/FEEDBACK.md` every iteration.
11. Stage only intended files for the current work.
12. Commit and push each work before starting the next.
13. Wait 60-90 seconds between iterations to respect rate limits.
14. Stop on preview, commit, or push failure after one repair attempt.
15. After each iteration, report work name, score/verdict, changed files, and commit hash.
