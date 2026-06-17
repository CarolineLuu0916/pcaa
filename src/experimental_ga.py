"""PCAA + GA-memory 联合条件 (experimental_ga)：Hard Persona 约束层 + GA-style 记忆子系统。

这是第四个实验条件，直接回答 §6.5 留下来的核心问题：
PCAA 的约束层能否在 GA-style 记忆（retrieval + reflection + planning）
的基础上带来额外增益？

条件对比矩阵：
┌─────────────────┬──────────────────┬───────────────────┐
│ 条件            │ Persona 注入     │ 记忆架构          │
├─────────────────┼──────────────────┼───────────────────┤
│ experimental    │ Hard Persona JSON│ 简单最近 5 条     │
│ baseline        │ 文本描述         │ 简单最近 5 条     │
│ baseline_ga     │ 文本描述         │ GA-style 完整流   │
│ experimental_ga │ Hard Persona JSON│ GA-style 完整流   │ ← 本文件
└─────────────────┴──────────────────┴───────────────────┘

关键假设：若 experimental_ga > baseline_ga，则说明 PCAA 约束层在任何记忆基础上都有增益，
而不只是因为对比对象的记忆系统比较弱。
"""
from __future__ import annotations

import json

from openai import OpenAI

from agent import RESPONSE_INSTRUCTIONS, RoundRecord, build_options_block, build_persona_block
from environment import apply_action_effects, apply_environment_effects, find_action_category, next_scenario
from ga_memory import GAMemoryStream
from llm_client import DEEPSEEK_MODEL, chat_json
from persona import TRAIT_ORDER, HardPersona, SoftState


def _generate_reflection(
    client: OpenAI,
    model: str,
    current: HardPersona,
    recent_entries: list,
) -> str:
    if not recent_entries:
        return ""
    memory_text = "\n".join(f"- {e.content}" for e in recent_entries)
    system_prompt = build_persona_block(current)
    user_prompt = (
        f"以下是你最近经历的事：\n{memory_text}\n\n"
        "请用第一人称提炼出 1-2 条更高层次的感悟"
        "（不是重复事件本身，而是从中归纳出的、关于你自己当下状态或倾向的认识）。"
        '只返回 JSON：{"reflection": "<1-2句话>"}'
    )
    result = chat_json(client, system_prompt, user_prompt, model=model, temperature=0.5)
    return result.get("reflection", "")


def _generate_plan(
    client: OpenAI,
    model: str,
    current: HardPersona,
    scenario: dict,
    retrieved: list,
) -> str:
    memory_text = "\n".join(f"- [{e.kind}] {e.content}" for e in retrieved) or "（暂无相关记忆）"
    system_prompt = build_persona_block(current)
    user_prompt = (
        f"当前场景：{scenario['name']} —— {scenario['description']}\n"
        f"相关记忆与反思：\n{memory_text}\n\n"
        "在做具体决定之前，先用一两句话给自己定一个这一刻的打算/心态基调"
        "（是大方向的意图，不是具体动作）。"
        '只返回 JSON：{"plan": "<一两句话的打算>"}'
    )
    result = chat_json(client, system_prompt, user_prompt, model=model, temperature=0.7)
    return result.get("plan", "")


def run_experimental_ga_agent(
    persona: HardPersona,
    scenarios: list[dict],
    rounds: int,
    client: OpenAI,
    model: str = DEEPSEEK_MODEL,
    drift_rate: float = 0.05,
) -> list[RoundRecord]:
    """PCAA 约束层 (Hard Persona JSON + 方向解读 + drift) 叠加 GA-style 记忆流。

    每个 timestep 比 experimental 多花 1-2 次 LLM 调用（planning 每轮 1 次，
    reflection 累计 importance 超过阈值时触发 1 次）。
    """
    initial_vector = persona.as_vector()
    current = persona
    soft_state = SoftState()
    stream = GAMemoryStream()
    records: list[RoundRecord] = []
    num_scenarios = len(scenarios)
    pending_signals: list[dict] = []

    for round_index in range(rounds):
        scenario = next_scenario(round_index, scenarios)
        soft_state = apply_environment_effects(soft_state, scenario)

        query = f"{scenario['name']}：{scenario['description']}"
        retrieved = stream.retrieve(query, current_round=round_index, k=5)

        if stream.should_reflect():
            reflection_text = _generate_reflection(
                client, model, current, stream.recent_observations(10),
            )
            if reflection_text:
                stream.add(reflection_text, round_index, client=client, model=model, kind="reflection")
            stream.reset_reflection_counter()
            retrieved = stream.retrieve(query, current_round=round_index, k=5)

        plan_text = _generate_plan(client, model, current, scenario, retrieved)

        memory_text = "\n".join(f"- [{e.kind}] {e.content}" for e in retrieved) or "（暂无相关记忆）"
        system_prompt = build_persona_block(current)
        user_prompt = (
            f"当前场景：{scenario['name']} —— {scenario['description']}\n"
            f"你当前的状态：心情={soft_state.mood}，精力={soft_state.energy:.2f}，"
            f"财富={soft_state.wealth:.0f}，疲劳度={soft_state.fatigue:.2f}\n"
            f"检索到的相关记忆/反思：\n{memory_text}\n"
            f"这一刻的打算：{plan_text}\n\n"
            f"{build_options_block(scenario)}\n\n"
            f"{RESPONSE_INSTRUCTIONS}"
        )
        response = chat_json(client, system_prompt, user_prompt, model=model)

        action_id = response["action_id"]
        action_category = find_action_category(scenario, action_id)
        behavior = response.get("behavior", "")
        mood = response.get("mood", soft_state.mood)

        soft_state = apply_action_effects(soft_state, action_category, mood)

        obs_text = f"第{round_index + 1}轮·{scenario['name']}：{behavior}（心情{mood}）"
        stream.add(obs_text, round_index, client=client, model=model, kind="observation")

        pending_signals.append(action_category["trait_signal"])
        is_meta_round_end = (round_index + 1) % num_scenarios == 0
        if is_meta_round_end:
            avg_signal = {
                k: sum(s[k] for s in pending_signals) / len(pending_signals)
                for k in TRAIT_ORDER
            }
            current = current.drift(avg_signal, rate=drift_rate)
            pending_signals = []

        records.append(RoundRecord(
            condition="experimental_ga",
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
            persona_vector_current=current.as_vector(),
            soft_state=soft_state.to_dict(),
        ))

    return records


if __name__ == "__main__":
    from environment import load_scenarios
    from llm_client import make_deepseek_client
    from persona import load_personas

    personas = load_personas("config/personas.json")
    scenarios = load_scenarios("config/scenarios.json")
    client = make_deepseek_client()

    target = personas[0]
    records = run_experimental_ga_agent(target, scenarios, rounds=3, client=client)
    for r in records:
        print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))
