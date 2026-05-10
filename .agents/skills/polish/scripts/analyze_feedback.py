import sys
import re
from collections import Counter
from pathlib import Path

def analyze_feedback(feedback_path: Path):
    if not feedback_path.exists():
        print("Feedback file not found.")
        return

    with open(feedback_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by work headers
    entries = re.split(r'\n## ', content)
    
    analysis = {
        "positive_keywords": Counter(),
        "negative_keywords": Counter(),
        "color_trends": Counter(),
        "style_preferences": Counter(),
        "recent_polish_requests": []
    }

    # Keywords to look for
    KEYWORDS = ["abstract", "realistic", "dense", "sparse", "dark", "bright", "neon", "organic", "geometric", "complex", "simple", "blurry", "sharp"]
    COLORS = ["gold", "obsidian", "cyan", "magenta", "teal", "amethyst", "indigo", "violet", "orange", "crimson", "mint", "silver", "white"]

    for entry in entries[1:]:  # Skip header
        lines = entry.split('\n')
        work_name = lines[0].strip()
        rating = ""
        comment = ""
        
        for line in lines:
            if "**Rating**" in line:
                rating = line.split(":", 1)[1].strip().lower()
            if "**Comment**" in line:
                comment = line.split(":", 1)[1].strip().lower()

        is_positive = any(x in rating for x in ["ok", "5/5", "good", "perfect", "stunning", "exceptional"])
        
        # Analyze words
        words = re.findall(r'\w+', comment)
        for word in words:
            if word in KEYWORDS:
                if is_positive:
                    analysis["positive_keywords"][word] += 1
                else:
                    analysis["negative_keywords"][word] += 1
            if word in COLORS:
                analysis["color_trends"][word] += 1
        
        if not rating and comment:
            analysis["recent_polish_requests"].append({"work": work_name, "comment": comment})

    print("--- Feedback Analytics ---")
    print("\nTop Positive Keywords (User Likes):")
    for k, v in analysis["positive_keywords"].most_common(5):
        print(f"- {k}: {v}")

    print("\nTop Negative/Friction Keywords:")
    for k, v in analysis["negative_keywords"].most_common(5):
        print(f"- {k}: {v}")

    print("\nPreferred Colors:")
    for k, v in analysis["color_trends"].most_common(5):
        print(f"- {k}: {v}")

    print("\nRecent Polish Targets (Blank Rating with Comment):")
    for req in analysis["recent_polish_requests"][:5]:
        print(f"- {req['work']}: \"{req['comment']}\"")

if __name__ == "__main__":
    feedback_file = Path(".agents/FEEDBACK.md")
    analyze_feedback(feedback_file)
