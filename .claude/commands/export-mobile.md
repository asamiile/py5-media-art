Follow `.agents/skills/export-mobile/SKILL.md` to create exactly one new py5 media art animation encoded for mobile playback.

Output spec: **MP4 / H.264 / 720p / 10–20s / seamless loop**

Execution rules:
1. Run one animation only.
2. Use branch `feature/works-YYYYMMDD`.
3. Check `git status --short` before starting. Stop if unrelated pending changes exist.
4. Set `SIZE = (1280, 720)` directly — do not use `get_sizes()`.
5. `DURATION_SEC` must be between 10 and 20.
6. Design for seamless loop: last frame must connect back to first.
7. Encode with FFmpeg: `libx264`, `profile:v baseline level 3.1`, `scale=1280:720`, `pix_fmt yuv420p`, `movflags +faststart`, `crf 23`.
8. Output filename: `sketch/{work_name}/{work_name}_mobile.mp4`.
9. Ensure `{work_name}_mobile.mp4` and `{work_name}_p1.png` exist before review.
10. Perform at most one revision.
11. Update `sketch/WORKS.md` and `.agents/FEEDBACK.md`.
12. Stage only intended files for this work.
13. Commit and push.
14. Report work name, critique verdict/score, changed files, and commit hash.
