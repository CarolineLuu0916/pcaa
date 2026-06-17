"""场景模板加载与确定性的环境/行为状态更新。

为了让结果可复现、可分析，Soft State 的数值变化（wealth/energy/fatigue）
完全由场景与 action_category 的预设效应决定，不依赖 LLM 输出的数字；
LLM 只负责在给定的封闭行为选项中做选择，并生成自然语言描述（behavior/mood）。
每个 action_category 还预先标定了 trait_signal 向量（设计者标定的"这个
选择像什么人格"的客观锚点），用于计算 persona consistency 和驱动 persona
drift，避免依赖模型自评导致的循环论证（模型直接复述注入的 persona 数值）。
"""
from __future__ import annotations

import json
from pathlib import Path

from persona import SoftState


def load_scenarios(path: str | Path) -> list[dict]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return data["scenarios"]


def next_scenario(round_index: int, scenarios: list[dict]) -> dict:
    """按轮次循环取场景模板（round_index 从 0 开始）。"""
    return scenarios[round_index % len(scenarios)]


def apply_environment_effects(soft_state: SoftState, scenario: dict) -> SoftState:
    eff = scenario["environment_effects"]
    wealth = soft_state.wealth
    if "wealth_delta_pct" in eff:
        wealth += soft_state.wealth * eff["wealth_delta_pct"]
    if "wealth_delta" in eff:
        wealth += eff["wealth_delta"]

    new_state = SoftState(
        mood=eff.get("mood_bias") or soft_state.mood,
        energy=soft_state.energy + eff.get("energy_delta", 0),
        wealth=wealth,
        fatigue=soft_state.fatigue + eff.get("fatigue_delta", 0),
        recent_events=list(soft_state.recent_events),
    )
    new_state.clamp()
    return new_state


def apply_action_effects(soft_state: SoftState, action_category: dict, mood_report: str) -> SoftState:
    new_state = SoftState(
        mood=mood_report or soft_state.mood,
        energy=soft_state.energy + action_category.get("energy_delta", 0),
        wealth=soft_state.wealth + action_category.get("wealth_delta", 0),
        fatigue=soft_state.fatigue + action_category.get("fatigue_delta", 0),
        recent_events=list(soft_state.recent_events),
    )
    new_state.clamp()
    return new_state


def find_action_category(scenario: dict, action_id: str) -> dict:
    for cat in scenario["action_categories"]:
        if cat["id"] == action_id:
            return cat
    raise ValueError(f"未知 action_category id={action_id!r}，scenario={scenario['id']!r}")
