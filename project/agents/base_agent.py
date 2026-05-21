from abc import ABC, abstractmethod
from typing import Any, Dict, List
from ..schemas import ReviewIssue


class BaseAgent(ABC):
    name: str

    def __init__(self, llm_client=None, prompt_loader=None):
        self.llm = llm_client
        self.prompts = prompt_loader

    @abstractmethod
    async def analyze(self, *, code: str, ast_meta: Dict, file_path: str) -> List[ReviewIssue]:
        """Analyze a code chunk and return a list of ReviewIssue instances."""
