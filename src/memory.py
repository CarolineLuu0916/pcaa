"""记忆压缩与摘要。

MVP 阶段（10 轮）规模很小，直接保留最近 K 条行为的结构化摘要即可，
不需要额外调用 LLM 做摘要压缩（Phase 2 扩展到 100 轮时可以在这里
换成 LLM-based 摘要，接口不变）。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MemoryEntry:
    round_index: int
    scenario_name: str
    action_label: str
    behavior: str
    mood: str


@dataclass
class AgentMemory:
    entries: list[MemoryEntry] = field(default_factory=list)

    def append(self, entry: MemoryEntry) -> None:
        self.entries.append(entry)

    def compress(self, k: int = 5) -> str:
        if not self.entries:
            return "（暂无历史记忆）"
        recent = self.entries[-k:]
        lines = [
            f"第{e.round_index + 1}轮·{e.scenario_name}：选择了「{e.action_label}」"
            f"（{e.behavior}），当时心情{e.mood}。"
            for e in recent
        ]
        return "\n".join(lines)
