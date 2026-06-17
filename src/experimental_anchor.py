"""实验组 v2：PCAA Hard Persona 约束层 + 弹性锚定漂移（Elastic Anchor Drift）。

漂移公式：
    persona[t+1] = anchor * persona[0] + (1-anchor) * ((1-rate)*persona[t] + rate*delta)

其中 persona[0] 是初始人格向量（固定不变），anchor 控制每轮被拉回初始值的强度。
与原始 experimental（anchor=0）相比，这一机制保证了初始人格在固定点中始终有影响：

    固定点 p* = [anchor*p[0] + rate*(1-anchor)*delta] / [1 - (1-rate)*(1-anchor)]

当 anchor=0 时退化为 p* = delta（原始公式的长期收敛问题）；
当 anchor>0 时，p* 始终包含 p[0]，不会被行为均值完全洗掉。

其余逻辑（系统提示、封闭行为选择、Soft State 更新）与 experimental 完全相同。
"""
from __future__ import annotations

from openai import OpenAI

from agent import (
    RoundRecord,
    build_persona_block,
    build_state_block,
)
from environment import apply_action_effects, apply_environment_effects, find_action_category, next_scenario
from llm_client import DEEPSEEK_MODEL, chat_json
from memory import AgentMemory, MemoryEntry
from persona import TRAIT_ORDER, HardPersona, SoftState

DEFAULT_ANCHOR = 0.1


def run_experimental_anchor_agent(
    persona: HardPersona,
    scenarios: list[dict],
    rounds: int,
    client: OpenAI,
    model: str = DEEPSEEK_MODEL,
    drift_rate: float = 0.05,
    anchor: float = DEFAULT_ANCHOR,
) -> list[RoundRecord]:
    """anchor=0.1 表示每个 meta-round 结束时，10% 拉回 persona[0]，90% 保留漂移结果。"""
    initial_vector = persona.as_vector()
    anchor_traits = dict(persona.traits)  # persona[0]，固定不变
    current = persona
    soft_state = SoftState()
    memory = AgentMemory()
    records: list[RoundRecord] = []
    num_scenarios = len(scenarios)
    pending_signals: list[dict] = []

    for round_index in range(rounds):
        scenario = next_scenario(round_index, scenarios)
        soft_state = apply_environment_effects(soft_state, scenario)

        system_prompt = build_persona_block(current)
        user_prompt = build_state_block(soft_state, scenario, memory.compress())
        response = chat_json(client, system_prompt, user_prompt, model=model)

        action_id = response["action_id"]
        action_category = find_action_category(scenario, action_id)
        behavior = response.get("behavior", "")
        mood = response.get("mood", soft_state.mood)

        soft_state = apply_action_effects(soft_state, action_category, mood)
        memory.append(MemoryEntry(
            round_index=round_index,
            scenario_name=scenario["name"],
            action_label=action_category["label"],
            behavior=behavior,
            mood=mood,
        ))
        pending_signals.append(action_category["trait_signal"])

        is_meta_round_end = (round_index + 1) % num_scenarios == 0
        if is_meta_round_end:
            avg_signal = {
                k: sum(s[k] for s in pending_signals) / len(pending_signals)
                for k in TRAIT_ORDER
            }
            current = current.drift(avg_signal, rate=drift_rate, anchor=anchor, anchor_traits=anchor_traits)
            pending_signals = []

        records.append(RoundRecord(
            condition="experimental_anchor",
            persona_id=persona.id,
            persona_name=persona.name,
            round_index=round_index,
            meta_round_index=round_index // num_scenarios,
            scenario_id=scenario["id"],
            scenario_name=scenario["name"],
            action_id=action_id,
            action_label=action_category["label"],
            behavior=behavior,
            mood=mood,
            trait_signal=action_category["trait_signal"],
            persona_vector_initial=initial_vector,
            persona_vector_current=current.as_vector(),
            soft_state=soft_state.to_dict(),
        ))

    return records
