Follow `.agents/skills/export-mobile/SKILL.md` to re-encode an existing artwork's video for mobile playback.

**Work name**: $ARGUMENTS
**Output spec**: MP4 / H.264 / 720p / 10–20s / seamless loop

Execution rules:
1. Use the work name from `$ARGUMENTS`. If empty, list available works in `sketch/` and ask which to export.
2. Verify `sketch/{work_name}/` exists and contains a source MP4.
3. Get source duration with `ffprobe`.
4. Determine target duration:
   - 10–20s source → keep as-is
   - < 10s → loop to 15s
   - > 20s → trim to 15s
5. Run FFmpeg with `-stream_loop -1 -t {TARGET_SEC}`, `libx264 baseline level 3.1`, `scale=1280:720`, `yuv420p`, `+faststart`, `crf 23`.
6. Output: `sketch/{work_name}/{work_name}_mobile.mp4`
7. Do not modify `main.py`, `WORKS.md`, or `FEEDBACK.md`.
8. Do not commit unless explicitly asked.
9. Report: work name, source duration, target duration, output path, file size.
