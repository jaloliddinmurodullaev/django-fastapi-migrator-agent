from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any
import json


class Phase(str, Enum):
    ANALYZE = "analyze"
    PLAN = "plan"
    EXECUTE = "execute"
    TEST = "test"
    DEBUG = "debug"
    VERIFY = "verify"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class AgentState:
    task: str
    project_path: str

    phase: Phase = Phase.ANALYZE
    plan: str = ""

    current_step: int = 0
    test_attempts: int = 0
    errors: list[str] = field(default_factory=list)

    context: dict[str, Any] = field(default_factory=dict)

    def save(self):
        state_dir = Path(self.project_path) / ".agent"
        state_dir.mkdir(exist_ok=True)

        state_file = state_dir / "state.json"

        data = asdict(self)
        data["phase"] = self.phase.value

        with state_file.open("w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False,
            )

    @classmethod
    def load(cls, project_path: str) -> "AgentState":
        state_file = Path(project_path) / ".agent" / "state.json"

        with state_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        data["phase"] = Phase(data["phase"])

        return cls(**data)