Execute `.agents/skills/export-mobile/SKILL.md` for work `$ARGUMENTS`:

1. If `sketch/$ARGUMENTS/output.mp4` is not present locally, fetch it from Google Drive via `uv run python scripts/upload_to_drive.py --fetch $ARGUMENTS`
2. Re-encode `sketch/$ARGUMENTS/output.mp4` into mobile-optimized H.264 10–20s seamless loop files:
   - Landscape (1280×720): `sketch/$ARGUMENTS/${ARGUMENTS}_landscape.mp4`
   - Portrait (720×1280): `sketch/$ARGUMENTS/${ARGUMENTS}_portrait.mp4`
3. Upload the generated mobile videos to Google Drive via `uv run python scripts/upload_to_drive.py $ARGUMENTS` (never commit `.mp4` files to git)
