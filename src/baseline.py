"""Baseline 对照组：纯 LLM，只给文本角色描述，不注入 Hard Persona JSON，
也没有 persona drift（CLAUDE.md 6.4.2：差异仅在于是否有结构化定量人格约束层）。
其余流程（场景、记忆、Soft State 更新、行为选项）与实验组完全一致，
确保两组唯一的自变量是"是否存在 Persona Constraint Layer"。
"""
from __future__ import annotations

import json

from openai import OpenAI

from agent import RoundRecord, build_options_block, RESPONSE_INSTRUCTIONS, sample_daily_nudge
from environment import apply_action_effects, apply_environment_effects, find_action_category, next_scenario
from llm_client import DEEPSEEK_MODEL, chat_json
from memory import AgentMemory, MemoryEntry
from persona import HardPersona, SoftState


def build_baseline_persona_block(persona: HardPersona) -> str:
    return (
        "你是一个有以下性格的人（仅用文字描述，不涉及任何具体数值）：\n"
        f"{persona.baseline_description}\n"
        "请始终按照这个人物的性格来行动和说话。"
    )


def build_baseline_state_block(soft_state: SoftState, scenario: dict, memory_text: str, daily_nudge: str = "") -> str:
    nudge_line = f"今日小情境：{daily_nudge}\n" if daily_nudge else ""
    return (
        f"当前场景：{scenario['name']} —— {scenario['description']}\n"
        f"你当前的状态：心情={soft_state.mood}，精力={soft_state.energy:.2f}，"
        f"财富={soft_state.wealth:.0f}，疲劳度={soft_state.fatigue:.2f}\n"
        f"{nudge_line}"
        f"最近的经历：\n{memory_text}\n\n"
        f"{build_options_block(scenario)}\n\n"
        f"{RESPONSE_INSTRUCTIONS}"
    )


def run_baseline_agent(
    persona: HardPersona,
    scenarios: list[dict],
    rounds: int,
    client: OpenAI,
    model: str = DEEPSEEK_MODEL,
    nudge_seed: int | None = None,
) -> list[RoundRecord]:
    """跑完一个 persona 在 baseline 条件下的完整轮次。

    persona 在这里只提供 baseline_description（文本）和 initial_vector
    （用于事后评测时的参照基准），从不作为结构化约束注入，也不漂移——
    baseline 没有 Constraint Layer，所以漂移这个概念对它不适用。
    """
    import random
    rng = random.Random(nudge_seed)

    initial_vector = persona.as_vector()
    soft_state = SoftState()
    memory = AgentMemory()
    records: list[RoundRecord] = []

    for round_index in range(rounds):
        scenario = next_scenario(round_index, scenarios)
        soft_state = apply_environment_effects(soft_state, scenario)

        daily_nudge = sample_daily_nudge(rng)
        system_prompt = build_baseline_persona_block(persona)
        user_prompt = build_baseline_state_block(soft_state, scenario, memory.compress(), daily_nudge=daily_nudge)
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

        records.append(RoundRecord(
            condition="baseline",
            persona_id=persona.id,
            persona_name=persona.name,
            round_index=round_index,
            meta_round_index=round_index // len(scenarios),
            scenario_id=scenario["id"],
            scenario_name=scenario["name"],
            action_id=action_id,
            action_label=action_category["label"],
            behavior=behavior,
            mood=mood,
            trait_signal=action_category["trait_signal"],
            persona_vector_initial=initial_vector,
            persona_vector_current=None,
            soft_state=soft_state.to_dict(),
        ))

    return records


if __name__ == "__main__":
    from llm_client import make_deepseek_client
    from persona import load_personas
    from environment import load_scenarios

    personas = load_personas("config/personas.json")
    scenarios = load_scenarios("config/scenarios.json")
    client = make_deepseek_client()

    target = personas[0]
    records = run_baseline_agent(target, scenarios, rounds=3, client=client)
    for r in records:
        print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))
