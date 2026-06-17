"""Persona-integrated GA (experimental_pga)：人格约束渗透进 GA 记忆管道的每一步。

与 experimental_ga（叠加式）的区别：
  experimental_ga   = PCAA system prompt  +  GA 记忆（两套机制并列，互不影响）
  experimental_pga  = PCAA 人格约束主动塑造 GA 记忆的 retrieval / reflection / planning

三处核心改动：
  1. Persona-grounded reflection：反思时显式要求对比行为与人格先验，产生"身份层感悟"
  2. Persona-weighted retrieval：检索记忆时加入人格相关度权重，有特质意义的记忆优先被召回
  3. Persona-anchored planning：planning 步骤明确以人格先验为出发点定义当轮意图
"""
from __future__ import annotations

from openai import OpenAI

from agent import RESPONSE_INSTRUCTIONS, RoundRecord, build_options_block, build_persona_block
from environment import apply_action_effects, apply_environment_effects, find_action_category, next_scenario
from ga_memory import GAMemoryEntry, GAMemoryStream, text_relevance
from llm_client import DEEPSEEK_MODEL, chat_json
from persona import TRAIT_ORDER, HardPersona, SoftState

_TRAIT_KEYWORDS = {
    "frugality":         "节俭 消费 花钱 储蓄 省钱 开销 购买 奢侈 节省",
    "social":            "社交 朋友 聚会 独处 人际 交流 互动 孤独 陪伴",
    "risk_appetite":     "风险 冒险 稳定 保守 机会 尝试 安全 挑战 不确定",
    "conscientiousness": "计划 自律 责任 拖延 认真 随性 目标 执行 规划",
    "openness":          "新鲜 尝试 传统 好奇 创新 保守 探索 变化 体验",
    "agreeableness":     "包容 妥协 坚持 随和 配合 争论 体谅 自我 和谐",
}


def _persona_context_string(persona: HardPersona) -> str:
    """把人格高权重维度的关键词拼成一段文本，用于计算记忆的人格相关度。"""
    parts = []
    for trait, value in persona.traits.items():
        if abs(value - 0.5) > 0.2:  # 只纳入与中间值有明显偏差的维度
            parts.append(_TRAIT_KEYWORDS.get(trait, ""))
    return " ".join(parts)


def _retrieve_with_persona(
    stream: GAMemoryStream,
    query: str,
    persona: HardPersona,
    current_round: int,
    k: int = 5,
    persona_weight: float = 0.3,
) -> list[GAMemoryEntry]:
    """在 GA 原有 recency+importance+relevance 基础上，加入人格相关度项。

    最终得分 = recency + importance_norm + (1-pw)*场景相关度 + pw*人格相关度
    pw=0.3 意味着 30% 的相关度权重来自人格，70% 来自场景。
    """
    if not stream.entries:
        return []
    persona_ctx = _persona_context_string(persona)
    scored = []
    for e in stream.entries:
        recency = stream.recency_decay ** max(0, current_round - e.last_accessed)
        importance_norm = e.importance / 10.0
        rel_scenario = text_relevance(query, e.content)
        rel_persona = text_relevance(persona_ctx, e.content) if persona_ctx else 0.0
        relevance = (1 - persona_weight) * rel_scenario + persona_weight * rel_persona
        scored.append((recency + importance_norm + relevance, e))
    scored.sort(key=lambda x: -x[0])
    top = [e for _, e in scored[:k]]
    for e in top:
        e.last_accessed = current_round
    return top


def _generate_reflection_pga(
    client: OpenAI,
    model: str,
    current: HardPersona,
    recent_entries: list[GAMemoryEntry],
) -> str:
    """双层反思：行为层（我做了什么）+ 人格层（这与我是谁的关系）。"""
    if not recent_entries:
        return ""
    memory_text = "\n".join(f"- {e.content}" for e in recent_entries)
    system_prompt = build_persona_block(current)
    user_prompt = (
        f"以下是你最近经历的事：\n{memory_text}\n\n"
        "请做两层反思，用第一人称写：\n"
        "1. 行为层：从这些经历里你观察到自己有什么行为倾向或模式？\n"
        "2. 人格层：对比你的人格先验（见系统提示中的数值），你最近的行为在哪里"
        "与你的特质吻合？哪里出现了偏离？这对你理解自己意味着什么？\n"
        "综合两层，用 1-2 句话写出最值得记住的感悟。"
        '只返回 JSON：{"reflection": "<1-2句话>"}'
    )
    result = chat_json(client, system_prompt, user_prompt, model=model, temperature=0.5)
    return result.get("reflection", "")


def _generate_plan_pga(
    client: OpenAI,
    model: str,
    current: HardPersona,
    scenario: dict,
    retrieved: list[GAMemoryEntry],
) -> str:
    """以人格先验为出发点定义当轮意图，而不是只看情境和记忆。"""
    memory_text = "\n".join(f"- [{e.kind}] {e.content}" for e in retrieved) or "（暂无相关记忆）"
    system_prompt = build_persona_block(current)
    user_prompt = (
        f"当前场景：{scenario['name']} —— {scenario['description']}\n"
        f"相关记忆与反思：\n{memory_text}\n\n"
        "在做具体决定之前，先基于你的人格先验（见系统提示）、结合当前情境和近期经历，"
        "用一两句话给自己定一个这一刻的打算/心态基调。"
        "你的打算应当体现出你的核心特质，同时也对当下具体情境有所回应。"
        '只返回 JSON：{"plan": "<一两句话的打算>"}'
    )
    result = chat_json(client, system_prompt, user_prompt, model=model, temperature=0.7)
    return result.get("plan", "")


def run_experimental_pga_agent(
    persona: HardPersona,
    scenarios: list[dict],
    rounds: int,
    client: OpenAI,
    model: str = DEEPSEEK_MODEL,
    drift_rate: float = 0.05,
    persona_weight: float = 0.3,
) -> list[RoundRecord]:
    """人格整合式 GA：人格约束渗透进 retrieval/reflection/planning 每一步。"""
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

        # 改动2：人格加权检索
        retrieved = _retrieve_with_persona(stream, query, current, round_index, k=5, persona_weight=persona_weight)

        if stream.should_reflect():
            # 改动1：人格双层反思
            reflection_text = _generate_reflection_pga(client, model, current, stream.recent_observations(10))
            if reflection_text:
                stream.add(reflection_text, round_index, client=client, model=model, kind="reflection")
            stream.reset_reflection_counter()
            retrieved = _retrieve_with_persona(stream, query, current, round_index, k=5, persona_weight=persona_weight)

        # 改动3：人格锚定规划
        plan_text = _generate_plan_pga(client, model, current, scenario, retrieved)

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
            condition="experimental_pga",
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
