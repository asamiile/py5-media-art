import re
from collections import Counter
from pathlib import Path

KEYWORDS = [
    "abstract", "realistic", "dense", "sparse", "dark", "bright", "light",
    "pastel", "vibrant", "monochrome", "minimal", "organic", "geometric",
    "complex", "simple", "blurry", "sharp", "smooth", "dynamic", "calm",
    "fluid", "architectural", "atmospheric", "contrast", "depth", "motion",
]

COLORS = [
    "ivory", "alabaster", "cream", "ochre", "terracotta", "celadon", "jade",
    "ultramarine", "cobalt", "vermilion", "amber", "emerald", "indigo",
    "violet", "crimson", "coral", "teal", "cyan", "magenta", "silver",
    "white", "charcoal", "gold", "obsidian",
]


def analyze_feedback(feedback_path: Path) -> None:
    if not feedback_path.exists():
        print(f"Feedback file not found: {feedback_path}")
        return

    content = feedback_path.read_text(encoding="utf-8")
    entries = re.split(r"\n## ", content)

    positive_keywords: Counter[str] = Counter()
    negative_keywords: Counter[str] = Counter()
    color_trends: Counter[str] = Counter()
    recent_polish_requests: list[dict[str, str]] = []

    for entry in entries[1:]:
        lines = entry.splitlines()
        if not lines:
            continue
        work_name = lines[0].strip()
        rating = ""
        comment = ""

        for line in lines:
            if "**Rating**" in line and ":" in line:
                rating = line.split(":", 1)[1].strip().lower()
            elif "**Comment**" in line and ":" in line:
                comment = line.split(":", 1)[1].strip().lower()

        is_positive = any(
            token in rating
            for token in ("ok", "5/5", "4/5", "good", "perfect", "stunning", "exceptional")
        )
        is_negative = any(token in rating for token in ("ng", "1/5", "2/5", "bad", "reject"))

        words = re.findall(r"\w+", comment)
        for word in words:
            if word in KEYWORDS:
                if is_positive:
                    positive_keywords[word] += 1
                elif is_negative or not is_positive:
                    negative_keywords[word] += 1
            if word in COLORS:
                color_trends[word] += 1

        if (not rating or is_negative) and comment:
            recent_polish_requests.append(
                {"work": work_name, "rating": rating or "(blank)", "comment": comment}
            )

    print("--- Feedback Analytics ---")
    print("\nTop Positive Keywords (User Likes):")
    for k, v in positive_keywords.most_common(8):
        print(f"- {k}: {v}")

    print("\nTop Negative/Friction Keywords:")
    for k, v in negative_keywords.most_common(8):
        print(f"- {k}: {v}")

    print("\nMentioned Palette Tokens:")
    for k, v in color_trends.most_common(8):
        print(f"- {k}: {v}")

    print("\nRecent Polish Targets (NG or Blank Rating with Comment):")
    for req in recent_polish_requests[:8]:
        print(f"- {req['work']} [{req['rating']}]: \"{req['comment']}\"")


if __name__ == "__main__":
    analyze_feedback(Path(".agents/FEEDBACK.md"))
