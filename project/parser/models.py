from pydantic import BaseModel
from typing import List, Optional


class NodeMetadata(BaseModel):
    name: str
    type: str
    line_start: int
    line_end: int
    imports_used: List[str] = []
    has_try_except: bool = False
    nested_loop_depth: int = 0
    dangerous_calls: List[str] = []
    cyclomatic_hint: int = 1
    docstring: Optional[str] = None
    decorators: List[str] = []
    inheritance: List[str] = []
