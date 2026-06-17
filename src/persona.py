"""Hard Persona (慢变量) 与 Soft State (动态变量) 的数据结构。"""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

TRAIT_ORDER = [
    "frugality",
    "social",
    "risk_appetite",
    "conscientiousness",
    "openness",
    "agreeableness",
]


@dataclass
class HardPersona:
    id: str
    name: str
    traits: dict[str, float]
    baseline_description: str

    def as_vector(self) -> list[float]:
        return [self.traits[k] for k in TRAIT_ORDER]

    def drift(
        self,
        trait_signal: dict[str, float],
        rate: float = 0.05,
        anchor: float = 0.0,
        anchor_traits: dict[str, float] | None = None,
    ) -> "HardPersona":
        """persona[t+1] = anchor * persona[0] + (1-anchor) * ((1-rate)*persona[t] + rate*delta)

        当 anchor=0 时退化为原始公式：(1-rate)*p[t] + rate*delta。
        当 anchor>0 时，每轮将 persona[0]（anchor_traits）以权重 anchor 混入，
        使初始人格始终对固定点有贡献，防止长期漂移完全收敛到行为均值。
        anchor_traits 应传入 persona[0].traits（初始值），不传时等同于 anchor=0。
        """
        new_traits = {}
        for k in TRAIT_ORDER:
            drifted = (1 - rate) * self.traits[k] + rate * trait_signal.get(k, self.traits[k])
            if anchor > 0 and anchor_traits:
                drifted = anchor * anchor_traits[k] + (1 - anchor) * drifted
            new_traits[k] = drifted
        return HardPersona(
            id=self.id,
            name=self.name,
            traits=new_traits,
            baseline_description=self.baseline_description,
        )

    def to_prompt_json(self) -> str:
        return json.dumps(self.traits, ensure_ascii=False, indent=2)


@dataclass
class SoftState:
    mood: str = "neutral"
    energy: float = 0.7
    wealth: float = 5000.0
    fatigue: float = 0.1
    recent_events: list[str] = field(default_factory=list)

    def clamp(self) -> None:
        self.energy = min(1.0, max(0.0, self.energy))
        self.fatigue = min(1.0, max(0.0, self.fatigue))

    def to_dict(self) -> dict:
        return asdict(self)


def load_personas(path: str | Path) -> list[HardPersona]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        HardPersona(
            id=p["id"],
            name=p["name"],
            traits=dict(p["traits"]),
            baseline_description=p["baseline_description"],
        )
        for p in data["personas"]
    ]
