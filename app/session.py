from dataclasses import dataclass, field

from .toolbox import ToolBox


@dataclass
class Session:
    id: str
    history: list[dict] = field(default_factory=list)  # OpenAI-style messages; yours to manage
    user_turns: int = 0  # how many user messages so far (set by main.py)
    toolbox: ToolBox = field(init=False)

    def __post_init__(self):
        self.toolbox = ToolBox(turn=lambda: self.user_turns)
