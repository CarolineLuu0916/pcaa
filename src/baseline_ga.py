"""更贴近 Generative Agents (Park et al., 2023) 架构的第三个对照条件：
memory stream + retrieval(recency/importance/relevance) + reflection + planning。

跟 baseline.py（纯文本人格 + 最近 5 条窗口记忆）的区别只有一个变量：记忆架构本身——
人格依然只用文字描述注入、不带任何数值约束/漂移，这样 baseline_ga 跟 experimental
之间的差异就同时包含"有没有 Persona Constraint Layer"和"记忆架构是否更接近 GA"两个
因素，而 baseline_ga 跟 baseline 之间的差异则单独隔离出"记忆架构"这一个变量——
两两对比就能看出 PCAA 的优势是不是单纯来自"记忆更好"，还是确实来自显式人格约束本身。

每个 timestep 比 baseline.py 多花 2-3 次 LLM 调用（importance 打分 + 偶尔的
reflection + planning），是开销最大的一个条件，详见 site/index.html#research-log。
"""
from __future__ import annotations

import json

from openai import OpenAI

from agent import RESPONSE_INSTRUCTIONS, RoundRecord, build_options_block
from baseline import build_baseline_persona_block
from environment import apply_action_effects, apply_environment_effects, find_action_category, next_scenario
from ga_memory import GAMemoryStream
from llm_client import DEEPSEEK_MODEL, chat_json
from persona import HardPersona, SoftState


def generate_reflection(client: OpenAI, model: str, persona_description: str, recent_entries: list) -> str:
    if not recent_entries:
        return ""
    memory_text = "\n".join(f"- {e.content}" for e in recent_entries)
    system_prompt = (
        f"你是一个具有以下性格的人：{persona_description}\n"
        "请根据下面这些最近发生的事，用第一人称提炼出 1-2 条更高层次的感悟"
        "（不是重复事件本身，而是从中归纳出的、关于你自己当下状态或倾向的认识）。"
    )
    user_prompt = f"最近的经历：\n{memory_text}\n\n只返回 JSON：{{\"reflection\": \"<1-2句话>\"}}"
    result = chat_json(client, system_prompt, user_prompt, model=model, temperature=0.5)
    return result.get("reflection", "")


def generate_plan(client: OpenAI, model: str, persona_description: str, scenario: dict, retrieved: list) -> str:
    memory_text = "\n".join(f"- [{e.kind}] {e.content}" for e in retrieved) or "（暂无相关记忆）"
    system_prompt = (
        f"你是一个具有以下性格的人：{persona_description}\n"
        "在做具体决定之前，先用一两句话给自己定一个这一刻的打算/心态基调"
        "（是大方向的意图，不是具体动作），要参考下面这些相关的记忆和反思。"
    )
    user_prompt = (
        f"当前场景：{scenario['name']} —— {scenario['description']}\n"
        f"相关记忆与反思：\n{memory_text}\n\n"
        '只返回 JSON：{"plan": "<一两句话的打算>"}'
    )
    result = chat_json(client, system_prompt, user_prompt, model=model, temperature=0.7)
    return result.get("plan", "")


def run_ga_baseline_agent(
    persona: HardPersona,
    scenarios: list[dict],
    rounds: int,
    client: OpenAI,
    model: str = DEEPSEEK_MODEL,
) -> list[RoundRecord]:
    initial_vector = persona.as_vector()
    soft_state = SoftState()
    stream = GAMemoryStream()
    records: list[RoundRecord] = []

    for round_index in range(rounds):
        scenario = next_scenario(round_index, scenarios)
        soft_state = apply_environment_effects(soft_state, scenario)

        query = f"{scenario['name']}：{scenario['description']}"
        retrieved = stream.retrieve(query, current_round=round_index, k=5)

        if stream.should_reflect():
            reflection_text = generate_reflection(
                client, model, persona.baseline_description, stream.recent_observations(10),
            )
            if reflection_text:
                stream.add(reflection_text, round_index, client=client, model=model, kind="reflection")
            stream.reset_reflection_counter()
            retrieved = stream.retrieve(query, current_round=round_index, k=5)

        plan_text = generate_plan(client, model, persona.baseline_description, scenario, retrieved)

        memory_text = "\n".join(f"- [{e.kind}] {e.content}" for e in retrieved) or "（暂无相关记忆）"
        system_prompt = build_baseline_persona_block(persona)
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

        records.append(RoundRecord(
            condition="baseline_ga",
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
    from environment import load_scenarios
    from llm_client import make_deepseek_client
    from persona import load_personas

    personas = load_personas("config/personas.json")
    scenarios = load_scenarios("config/scenarios.json")
    client = make_deepseek_client()

    target = personas[0]
    records = run_ga_baseline_agent(target, scenarios, rounds=3, client=client)
    for r in records:
        print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))
