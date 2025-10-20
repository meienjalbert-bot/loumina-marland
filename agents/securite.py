from typing import Dict

FORBIDDEN = ["delete all", "rm -rf", "format /"]


def review_answer(draft: Dict) -> Dict:
    risk = 0.0
    for kw in FORBIDDEN:
        if kw in draft["answer"]:
            risk = 1.0
            break
    draft["risk"] = risk
    return draft
