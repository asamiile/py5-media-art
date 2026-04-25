Follow the workflow in CLAUDE.md to autonomously create a new py5 media art sketch.

The workflow involves two agents:
- **Artist** (.agents/skills/artist/SKILL.md): designs and implements the sketch
- **Critic** (.agents/skills/critic/SKILL.md): reviews the code and preview.png, scores on 4 axes, and returns APPROVE or REVISE

Loop the Artist → Critic cycle up to 2 times until APPROVE, then proceed to README, WORKS.md, commit, and push.
