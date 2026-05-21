import ast
import difflib
from typing import List, Dict
from ..logging_config import get_logger

logger = get_logger("sentinelai.autofix.suggester")


def suggest_auto_fix(code: str, issue: Dict) -> Dict:
    """Return a suggested patch dict for simple patterns.

    Returns: {patch: str, diff: str}
    """
    title = issue.get("title", "").lower()
    lines = code.splitlines()
    new_lines = list(lines)
    changed = False

    if "eval" in title:
        # naive replacement: replace eval( with ast.literal_eval(
        for i, l in enumerate(new_lines):
            if "eval(" in l:
                new_lines[i] = l.replace("eval(", "ast.literal_eval(")
                changed = True

    if "broad except" in title or "except" in title and "Exception" in title:
        # suggest narrowing excepts - this is only illustrative
        for i, l in enumerate(new_lines):
            if l.strip().startswith("except:"):
                new_lines[i] = l.replace("except:", "except Exception as e:")
                changed = True

    if not changed:
        return {"patch": "", "diff": ""}

    patched = "\n".join(new_lines)
    diff = "\n".join(difflib.unified_diff(lines, new_lines, lineterm=""))
    return {"patch": patched, "diff": diff}
