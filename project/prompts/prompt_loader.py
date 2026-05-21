from pathlib import Path
from typing import Dict
from ..logging_config import get_logger

logger = get_logger("sentinelai.prompts.loader")


class PromptLoader:
    def __init__(self, prompts_dir: Path):
        self.prompts_dir = Path(prompts_dir)
        self.mode = "Senior Engineer"

    def load(self, name: str) -> str:
        p = self.prompts_dir / f"{name}.txt"
        if not p.exists():
            logger.error("Prompt not found: %s", p)
            raise FileNotFoundError(p)
        return p.read_text(encoding="utf-8")

    def build_prompt(self, template_name: str, *, role: str, ast_meta: Dict, code: str, mode: str = None) -> str:
        tmpl = self.load(template_name)
        if mode:
            self.mode = mode
        # Deterministic formatting: include JSON-serializable AST metadata
        ast_block = "\n".join([f"{k}: {v}" for k, v in ast_meta.items()])
        prompt = tmpl + "\n\n" + (
            f"MODE: {self.mode}\nROLE: {role}\n---\nAST_METADATA:\n{ast_block}\n---\nCODE:\n{code}\n\n"
        )
        # Force instructions for strict JSON
        prompt += (
            "Respond ONLY with a single JSON array of objects following the ReviewIssue schema."
            " Do not include markdown or explanatory text."
        )
        return prompt
