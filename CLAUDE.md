# PCAA: Persona-Constrained Agent Architecture

> **给 Claude Code 的项目上下文文件。请完整阅读后再开始工作。**

---

## 一、项目目标

系统性验证一个假设：

> **人格（Persona）应该是 Agent 的先验（Prior），而不是后验（Posterior）。**

当前主流 Agent（如 Stanford Generative Agents）的范式是：**行为 → 记忆 → 反思 → 形成人格**。本项目验证反向范式：**固定人格 → 约束行为边界 → 与环境交互 → 产出行为**。

最终产出：一篇可提交 arXiv 的短论文（short paper / workshop paper），核心贡献是证明 **Persona Constraint Layer 能缓解 Agent 同质化（homogenization）并提升长期行为一致性**。

---

## 二、核心架构

### 形式化定义

```
Behavior = f(Persona, Memory, Environment, Event, Randomness)
```

| 变量 | 含义 | 稳定性 |
|------|------|--------|
| Persona | 稳定人格特质 | 95% 继承，5% 漂移 |
| Memory | 历史经验积累 | 持续更新 |
| Environment | 当前环境/场域 | 每轮由场景决定 |
| Event | 突发事件 | 随机注入 |
| Randomness | 噪声/偶然性 | 每轮随机种子 |

### 两层人格模型

**第一层：Hard Persona（硬人格，几乎不可变）**

```json
{
  "frugality": 0.9,      // 节俭度 [0-1]
  "social": 0.2,         // 社交性 [0-1]
  "risk_appetite": 0.1,  // 风险偏好 [0-1]
  "conscientiousness": 0.8, // 责任心 [0-1]
  "openness": 0.3,       // 开放性 [0-1]
  "agreeableness": 0.5   // 宜人性 [0-1]
}
```

更新规则：每轮 `persona[t+1] = 0.95 * persona[t] + 0.05 * delta`（慢漂移）。

**第二层：Soft State（软状态，动态变化）**

```json
{
  "mood": "neutral",     // happy / neutral / sad / anxious
  "energy": 0.7,         // [0-1]
  "wealth": 5000,        // 当前财富
  "fatigue": 0.1,        // 疲劳度 [0-1]
  "recent_events": []    // 近期事件影响
}
```

每轮完整更新，由 Environment + Event 驱动。

### 行为决策公式

```
ActionScore[i] = 
    0.50 × persona_weight[i]     // 人格倾向（主导）
  + 0.25 × memory_weight[i]     // 经验影响
  + 0.15 × environment_weight[i] // 情境调整
  + 0.05 × random_noise          // 偶然性

最终行为 = Softmax(ActionScore) → 概率采样 Top-K
```

核心原则：**人格决定决策的概率分布，而不是机械决定具体行为。**
- 吝啬的人（frugality=0.9）不是永远不去米其林，只是去米其林的概率是 5% 而不是 50%
- 内向的人（social=0.2）不是永远不参加聚会，只是概率更低

---

## 三、实验设计

### 3.1 MVP（最小可行实验）

| 参数 | 值 |
|------|-----|
| Persona 类型 | 3 种（吝啬内向型 / 开放社交型 / 谨慎稳定型） |
| 实验条件 | 2 种（有 Persona Lock / 无纯 LLM Baseline） |
| Agent 总数 | 3 × 2 = 6 |
| 模拟轮次 | 10 轮 |
| 场景模板 | 5 个（日常/涨工资/失业/社交邀请/突发疾病） |
| 总 agent-round | 300 |

### 3.2 完整实验

| 参数 | 值 |
|------|-----|
| Persona 类型 | 10 种（Big Five 维度系统采样） |
| 模拟轮次 | 100 轮 |
| 场景模板 | 10 个 |
| Agent 总数 | 20 |
| 总 agent-round | 20,000 |

### 3.3 对照组设计

- **Baseline 组**：纯 LLM，只有 Memory 摘要 + 当前环境，无 Hard Persona。角色设定仅通过 prompt 描述。
- **Experimental 组**：PCAA 完整管线，Hard Persona JSON 注入系统 prompt，每轮经过 Persona Constraint 过滤。

### 3.4 环境/事件生成器

场景模板（每个场景包含 Environment + Event）：

1. **日常一天** — 正常工作日，无特殊事件
2. **涨工资** — 收入 +30%，消费倾向临时 +0.3
3. **失业** — 收入归零，焦虑 mood，消费倾向 -0.5
4. **社交邀请** — 朋友邀请聚会/旅行，社交性权重临时提升
5. **突发疾病** — energy -0.5, fatigue +0.5, 需医疗支出
6. **结婚纪念日** — mood=happy, 消费倾向临时 +0.6
7. **市场崩盘** — wealth -40%, risk_appetite -0.3
8. **升职机会** — 需要决策是否接受（权衡风险/责任/收入）
9. **邻里冲突** — agreeableness 被挑战
10. **独自旅行** — openness 被激活，社交需求降低

---

## 四、评测指标

### 4.1 Persona Consistency（人格一致性）

- **方法**：对比初始 Hard Persona 与 100 轮后的行为模式
- **指标**：Cosine Similarity（行为向量 vs 初始人格向量）
- **验证**：LLM-as-a-Judge 打分（1-5，判断行为是否符合初始人设）
- **假设**：实验组 > 对照组

### 4.2 Behavioral Diversity（行为多样性）

- **方法**：统计所有 Agent 在所有轮次的行为分布
- **指标**：Shannon Entropy
- **验证**：检查实验组是否保持了多样性（不因 Persona Lock 而僵化）
- **陷阱**：Persona Lock 不应该导致所有 Agent 行为雷同

### 4.3 Social Realism（社会真实感）

- **方法**：从两组中各抽样 20 个行为轨迹
- **指标**：A/B 盲测 — 让真人（或 GPT-4o Judge）判断"哪个更像真实人类"
- **假设**：实验组 > 对照组

### 4.4 Long-term Stability（长期稳定性）

- **方法**：追踪 100 轮中行为模式的变化曲线
- **指标**：滚动窗口 Cosine Similarity（窗口长度 = 10 轮）
- **验证**：观察人格是否在后期崩塌（drift）

---

## 五、文献基础

### 5.1 AI/ML 必读（Baseline & 对比）

| 论文 | 年份 | arXiv | 作用 |
|------|------|-------|------|
| Generative Agents: Interactive Simulacra of Human Behavior | 2023 | 2304.03442 | 你要超越的 baseline |
| MemGPT: Towards LLMs as Operating Systems | 2023 | 2310.08560 | 长期记忆 SOTA |
| ReAct: Synergizing Reasoning and Acting in Language Models | 2023 | 2210.03629 | 推理-行动循环 |
| CAMEL: Communicative Agents for "Mind" Exploration | 2023 | 2303.17760 | 多 Agent 协作 |
| Voyager: An Open-Ended Embodied Agent with LLMs | 2023 | 2305.16291 | 技能学习 |
| Reflexion: Language Agents with Verbal Reinforcement Learning | 2023 | 2303.11366 | 自我反思 |
| Constitutional AI: Harmlessness from AI Feedback | 2022 | 2212.08073 | 最接近"人格宪法"思路 |

### 5.2 心理学/社会学理论支撑（论证创新性用）

| 学者 | 著作/论文 | 年份 | 核心概念 | 映射到 PCAA |
|------|----------|------|---------|------------|
| Kurt Lewin | Principles of Topological Psychology | 1936 | B = f(P, E) — 行为是人与环境的函数 | 你的公式的学科祖先 |
| Pierre Bourdieu | Le Sens Pratique (The Logic of Practice) | 1980 | Habitus（惯习）= 持久倾向系统，划定行为边界 | Hard Persona |
| Erving Goffman | The Presentation of Self in Everyday Life | 1956 | 拟剧论：前台/后台行为，情境自我 | Environment 参数 |
| Walter Mischel & Yuichi Shoda | A Cognitive-Affective System Theory of Personality | 1995 | CAPS 模型：人-情境交互，人格稳定+情境敏感 | 两层 Persona 设计 |
| Anthony Giddens | The Constitution of Society | 1984 | 结构化理论：结构约束行动，行动再生产结构 | Memory 微调 Persona |
| George Herbert Mead | Mind, Self, and Society | 1934 | "I" vs "Me"，自我从社会互动中涌现 | Agent-Agent 交互 |
| William Fleeson | Toward a structure- and process-integrated view of personality | 2001 | 人格密度分布（density distributions） | 概率行为而非确定行为 |

### 5.3 2025-2026 最新（你的机会窗口）

关键词搜索建议：
- `persona drift in LLM agents`
- `agent homogenization`
- `persona fidelity long-term simulation`
- `character consistency LLM`
- `persona-conditioned memory`

已知一篇高度相关：
- *From Facts to Insights: A Persona-Driven Dual Memory Framework and Dataset for Role-Playing Agents* (2026) — 提出 persona-conditioned memory，非常接近你的思路，需要找原文对比

---

## 六、技术实现指南

### 6.1 API 选型

| 用途 | 推荐模型 | 输入价格/1M | 输出价格/1M |
|------|---------|------------|------------|
| Agent 行为生成 | DeepSeek V3 | $0.27 | $1.10 |
| LLM-as-a-Judge 评测 | GPT-4o | $2.50 | $10.00 |

**完整实验费用**：行为 ~$33 + 评测 ~$5 = **~$38**（用 DeepSeek）

### 6.2 项目结构建议

```
pcaa-experiment/
├── CLAUDE.md                 # 本文件
├── config/
│   ├── personas.json         # 10 个预定义 Persona
│   └── scenarios.json        # 环境/事件模板
├── src/
│   ├── agent.py              # Agent Loop（含 Persona Constraint）
│   ├── persona.py            # Hard Persona + Soft State 数据结构
│   ├── environment.py        # 场景事件生成器
│   ├── memory.py             # 记忆压缩与摘要
│   ├── baseline.py           # 纯 LLM 对照组
│   └── judge.py              # LLM-as-a-Judge 评测
├── experiments/
│   ├── run_mvp.py            # MVP 实验（300 agent-round）
│   └── run_full.py           # 完整实验（20,000 agent-round）
├── analysis/
│   ├── consistency.py        # 人格一致性分析
│   ├── diversity.py          # 行为多样性分析
│   └── visualize.py          # 图表生成
├── results/                  # 实验输出（JSONL + 图表）
└── paper/
    └── draft.md              # 论文草稿
```

### 6.3 Agent Loop 伪代码

```python
def agent_loop(persona, soft_state, memory, environment, event, rounds=100):
    history = []
    for round in range(rounds):
        # 1. 注入 Persona Constraint
        system_prompt = build_persona_prompt(persona)
        
        # 2. 注入当前状态
        state_prompt = build_state_prompt(soft_state, environment, event)
        
        # 3. 注入记忆摘要
        memory_summary = compress_memory(memory)
        
        # 4. 调用 LLM 生成行为
        behavior = call_llm(system_prompt + state_prompt + memory_summary)
        
        # 5. 记录行为
        history.append(behavior)
        
        # 6. 更新 Soft State
        soft_state = update_soft_state(soft_state, environment, event, behavior)
        
        # 7. 更新 Memory
        memory.append(behavior)
        
        # 8. 慢漂移 Persona（5% 噪声）
        persona = drift_persona(persona, rate=0.05)
        
        # 9. 生成下一轮环境/事件
        environment, event = next_scenario()
    
    return history
```

### 6.4 关键实现注意点

1. **Persona Constraint 不是硬过滤**：不要用 `if frugality > 0.8: reject expensive action`。而是把 persona 权重注入 prompt，让 LLM 在推理时自动倾向吝啬行为。这样更自然、更可泛化。

2. **Baseline 的 prompt 要公平**：对照组也要给角色描述（"你是一个吝啬内向的人"），但不能给数值化的 Hard Persona JSON。差异仅在于是否有**结构化的定量人格约束层**。

3. **评测时 blinding**：LLM-as-a-Judge 不应该知道哪个轨迹来自实验组哪个来自对照组。

4. **温度参数**：行为生成用 temperature=0.7（保留随机性），评测用 temperature=0（一致性）。

5. **结果要可复现**：固定所有随机种子，记录到实验日志。

---

## 七、贡献陈述（论文用）

### 一句话贡献

> We propose Persona-Constrained Agent Architecture (PCAA), which treats persona as a Bayesian prior constraining behavior generation, rather than a posterior label emergent from behavior — addressing the agent homogenization problem in long-term multi-agent simulations.

### 三个具体贡献

1. **概念贡献**：将人格从"行为总结的标签"重新定义为"行为生成的约束条件"，并通过两层人格模型（Hard Persona + Soft State）实现
2. **实证贡献**：通过对照实验证明 Persona Lock 能显著提升长期模拟中的人格一致性同时保持行为多样性
3. **学科交叉贡献**：将 Bourdieu 的 Habitus、Lewin 的场论、Mischel 的 CAPS 模型引入 Agent 架构设计

---

## 八、你的任务（给 Claude Code）

请按以下优先级完成：

### Phase 1：MVP（先跑通再扩展）

1. **搭建项目骨架** — 按上述目录结构创建项目
2. **实现 3 个预定义 Persona** — 吝啬内向型 / 开放社交型 / 谨慎稳定型
3. **实现 5 个场景模板** — 日常/涨工资/失业/社交邀请/突发疾病
4. **实现 Agent Loop** — 集成 DeepSeek API（用 `OPENAI_API_BASE=https://api.deepseek.com` + `deepseek-chat` 模型）
5. **实现 Baseline** — 纯 LLM 对照组（无 Hard Persona JSON）
6. **跑 MVP 实验** — 3 persona × 2 条件 × 5 场景 × 10 轮 = 300 agent-round
7. **实现 LLM-as-a-Judge 评测** — 用 GPT-4o 打分
8. **输出结果** — 一致性分数、多样性熵值、数据表格

### Phase 2：扩展（MVP 通过后）

9. **扩展至 10 Persona** — 基于 Big Five 系统采样
10. **扩展至 10 场景 + 100 轮**
11. **完整实验跑 20,000 agent-round**
12. **生成图表** — 人格漂移曲线、行为多样性对比、显著性检验
13. **撰写论文草稿** — 填充 paper/draft.md

### 约束

- API key 从环境变量读取：`DEEPSEEK_API_KEY`、`OPENAI_API_KEY`
- 所有实验参数可配置、可复现
- 结果以 JSONL 格式存储，每行一个 agent-round
- Python 3.11+，依赖放 requirements.txt
- 优先用 DeepSeek 跑行为生成以控制成本
