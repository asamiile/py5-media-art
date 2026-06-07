---
name: write-medium-article
description: "Analyzes a py5 media art sketch and generates a Medium-ready technical article in Markdown. Output goes to medium/YYYY-MM-DD_{work_name}_medium.md. Triggers: write medium article, blog post, medium draft, write article about"
allowed-tools: Bash, Read, Write
---

# Write Medium Article Skill

Generate a high-quality English technical article for Medium about one specified py5 media art sketch.

## Invocation

The user provides the target work name as an argument:
```
/write-medium-article {work_name}
```
If no argument is given, ask the user which work to write about before proceeding.

## Workflow

### 1. Identify and read source files

- `work_name` = the argument provided by the user.
- Confirm `sketch/{work_name}/` exists. Stop and report an error if it does not.
- **Always read**: `sketch/{work_name}/main.py`
- **Read if it exists**: `sketch/{work_name}/README.md`
- **Read the matching entry** from `sketch/WORKS.md` (find the `## {work_name}` heading and read its Date, Theme, Technique, and Description fields).
- If README.md is absent, derive article content entirely from main.py analysis and the WORKS.md entry.

### 2. Generate the article

Write the article to `medium/{today_YYYY-MM-DD}_{work_name}_medium.md`.

- Create the `medium/` directory if it does not exist.
- If a file with the same name already exists, overwrite it.
- Do **not** include YAML front-matter. Start directly with `# Title`.

### 3. Report

Print the article title and output file path. Remind the user to open the file and paste its contents into Medium's editor.

---

## Article Structure

### 1. Title
Catchy and professional title for a tech/creative coding audience. Include the core visual concept. Keep it under 80 characters.

### 2. Introduction (2–3 paragraphs)
- What is this work? The core visual concept and motivation in one sentence.
- Describe the visual result a reader can picture without seeing it.
- Why Python / py5 was the right tool for this particular idea.

### 3. Visual & Aesthetic Approach
- Rendering technique, geometry, lighting model, and color palette.
- Key algorithms: noise functions, particle systems, 3D math, shader-equivalent tricks in py5, etc.
- **Tone**: cinematic and realistic. Do not reference anime, cartoon, or stylized aesthetics.

### 4. Code & Technical Breakdown
- Identify the 2–3 most important functions or sections in `main.py`.
- Show critical code blocks (10–30 lines each) with inline explanation.
- Explain *why* the technique works, not just what the code does.
- Prefer depth on one key idea over shallow coverage of many.

### 5. Conclusion & CTAs
- One paragraph: what makes this work interesting or what you learned.
- Link block (use these exact URLs):
  - Youtube: https://youtube.com/playlist?list=PL5Uiqt5oXo0HR6D_6HbPiDWkYEQUHo1UD&si=7HVBp54ZErUnb2_f
  - GitHub: https://github.com/asamiile/py5-media-art/tree/main/sketch/{work_name}
  - Portfolio: https://asami.tokyo
  - Purchase assets: https://stock.adobe.com/jp/contributor/211325934/asamiile?load_type=author&prev_url=detail
  - Project Support: https://buymeacoffee.com/asamiile

---

## Tone & Style

| Parameter   | Spec                                                      |
|-------------|-----------------------------------------------------------|
| Audience    | Developers, engineers, creative coders                    |
| Tone        | Logical, insightful, concise, professional — not hype-y   |
| Language    | English only                                              |
| Length      | 800–1200 words                                            |
| Format      | Strict Markdown. No YAML front-matter.                    |

---

## Constraints

- Do **not** stage, commit, or push any files.
- Do **not** modify any sketch files or WORKS.md.
- Do **not** run any scripts or the sketch.
- Output only to `medium/` directory.
- Do **not** use Markdown image syntax (`![alt](url)`) — Medium's editor cannot render it.
- Do **not** use Markdown tables — Medium's editor does not support them.
