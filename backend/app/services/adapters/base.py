"""Adapter base — all root methods MUST define prerequisites, steps,
verification, and recovery. No adapter may expose arbitrary shell."""
from dataclasses import dataclass, field


@dataclass
class OpStep:
    name: str
    description: str
    destructive: bool = False
    expected_result: str = ""
    verification: str = ""  # how the client verifies this step
    timeout_seconds: int = 120


@dataclass
class AdapterSpec:
    method: str
    prerequisites: list[str]
    steps: list[OpStep]
    recovery: list[str]
    verification_checks: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "prerequisites": self.prerequisites,
            "steps": [
                {"name": s.name, "description": s.description, "destructive": s.destructive,
                 "expected_result": s.expected_result, "verification": s.verification,
                 "timeout_seconds": s.timeout_seconds}
                for s in self.steps
            ],
            "recovery": self.recovery,
            "verification_checks": self.verification_checks,
        }
