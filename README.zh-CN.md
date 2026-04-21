# 情绪.skill / Emotion Skill

[English README](./README.md)

面向 Coding Agent 的情绪感知编排层。

这个仓库会读取最新用户消息，以及可选的历史对话、运行时信号和用户画像，然后输出优先级、验证强度、回复风格、收口模式、review pass 提示这些工作模式信号。

## 仓库里有什么

- `SKILL.md`：skill 定义和完整输入契约
- `scripts/emotion_engine.py`：规则引擎和 CLI
- `scripts/alignment_test.py`：回归样例集
- `scripts/ablation_test.py`：skill 与静态基线的对比评测
- `scripts/smoke_test.py`：带本地历史和随机社区工作流的场景烟测
- `scripts/independent_audit.py`：独立契约与宿主画像边界审计
- `scripts/marketplace_tag_audit.py`：ClawHub 市场标签回归、评测与烟测
- `scripts/minimal_host_adapter.py`：带宿主本地画像复用的最小可用适配器
- `demo/local_history_event.json`：真实感 demo payload
- `references/`：设计说明、案例、提示词参考

## 适合什么场景

- Coding Agent 面对赶时间、重复失败、用户质疑、边界保护、成功后收口这类对话
- 宿主侧能调用本地 Python 脚本，并消费 JSON 输出

## 市场定位

- repository debugging
- coding-agent 编排
- 验证强度控制
- 队列、线程、heartbeat 协调
- 成功后的稳定收口

## 核心输入

引擎接收一个 JSON payload。最常用的字段有：

- `message`
- `history`
- `runtime`
- `user_profile`
- `last_state`
- `llm_semantic`
- `posthoc_semantic`
- `calibration_state`

完整字段说明和示例放在 [SKILL.md](./SKILL.md)。

## 核心输出

先接这两个：

- `overlay_prompt`：当前这一轮的紧凑运行时提示
- `routing.thread_interface`：队列模式、主线程偏好、heartbeat 行为、并行度、进度更新间隔

常用补充输出：

- `guidance`
- `memory_update`
- `posthoc_plan`
- `prompts`

## 安装

环境要求：

- Python `3.9+`
- 无第三方依赖

先拉仓库：

```bash
git clone https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill.git
cd emotion-skill-qingxu-skill
```

如果你想按 Codex 风格作为本地 skill 使用，可以复制到本地 skills 目录。

macOS / Linux:

```bash
cp -r emotion-skill-qingxu-skill ~/.codex/skills/emotion-skill
```

PowerShell:

```powershell
Copy-Item -LiteralPath .\emotion-skill-qingxu-skill -Destination $HOME\.codex\skills\emotion-skill -Recurse -Force
```

## 快速开始

先用单条消息做烟测：

```bash
python scripts/emotion_engine.py run --message "先给我依据，别瞎猜" --pretty
```

再跑仓库自带的本地历史 demo：

```bash
python scripts/emotion_engine.py run --input demo/local_history_event.json --pretty
```

再用完整 payload 跑一轮：

```bash
python scripts/emotion_engine.py run --input path/to/turn.json --pretty
```

如果你想直接接一个带宿主本地画像的最小宿主：

```bash
python scripts/minimal_host_adapter.py --event demo/local_history_event.json --store-dir .demo-store --pretty
```

最小 payload 示例：

```json
{
  "message": "这个问题还没修好，先给我依据，再继续改。",
  "history": [
    {"role": "assistant", "text": "我觉得已经定位到根因了"}
  ],
  "runtime": {
    "response_delay_seconds": 20,
    "unresolved_turns": 3,
    "bug_retries": 2,
    "same_issue_mentions": 2
  }
}
```

## 接入路径

1. 每轮用户消息都调用一次 `emotion_engine.py`。
2. 把 `overlay_prompt` 插进当前这轮 prompt，作为紧凑的动态前置提示。
3. 把 `routing.thread_interface` 接到队列、主线程选择、heartbeat 和进度节奏控制。
4. 当 `analysis.semantic_pass` 是 `fast` 时，再补跑模型语义判断，并把结果按 `llm_semantic` 回填。
5. 如果你需要跨轮自适应，就把 `memory_update` 里的有限字段复用到宿主自有的本地画像里。

## 它重点优化哪些状态

| 状态 | 主要行为变化 | 价值 |
|---|---|---|
| `urgent` | 抢主线程，缩短进度更新间隔 | 更快给出第一个有效动作 |
| `frustrated` | 先修再解释 | 降低漂移，减少废话 |
| `skeptical` | 先给依据和校验点 | 降低盲改和误诊 |
| `cautious` | 收紧 scope，优先安全路径 | 降低越界修改 |
| `satisfied` | 进入 guard mode | 降低成功后的回归风险 |

## 语言覆盖

当前特化校准重点覆盖：

- 中文
- 英文

其他语言当前主要走通用路径，依赖标点强度、重复、延迟压力、多轮未解决压力和命令式结构。

## 产品边界

- 运行时适配层放在宿主侧
- 跨轮自适应通过宿主自有本地画像复用 `memory_update` 的有限字段
- 下方评测数字来自仓库内置的精选样例
- 第一轮判断在带有 `runtime` 和 `history` 时更稳
- 市场定位就是 coding-agent 编排层

## 当前状态

我在这个仓库里的本地运行结果：

- alignment regression：`50/50`
- curated ablation harness：`201/201`
- 同一套评分下的静态基线：`6/201`
- 场景烟测：`ok`
- 独立审计：`ok`
- ClawHub 标签审计：`ok`
- feature gate 审计：`ok`

这些数字更适合解读成回归覆盖率和规则稳定性，不适合直接当成线上 A/B 结论。

ClawHub 发布包只带运行时所需子集。更重的回归、审计和校准资产继续留在 GitHub 仓库。

## 仓库结构

ClawHub 发布包内：

- [SKILL.md](./SKILL.md)：skill 定义和完整契约
- [scripts/emotion_engine.py](./scripts/emotion_engine.py)：运行时引擎
- [scripts/minimal_host_adapter.py](./scripts/minimal_host_adapter.py)：带宿主本地画像的最小宿主适配器
- [demo/local_history_event.json](./demo/local_history_event.json)：真实本地历史 demo payload
- [references/examples.md](./references/examples.md)：案例输入输出

GitHub 仓库内额外保留：

- [scripts/alignment_test.py](./scripts/alignment_test.py)：回归样例集
- [scripts/ablation_test.py](./scripts/ablation_test.py)：评测脚本
- [scripts/smoke_test.py](./scripts/smoke_test.py)：场景烟测
- [scripts/independent_audit.py](./scripts/independent_audit.py)：独立校验
- [scripts/marketplace_tag_audit.py](./scripts/marketplace_tag_audit.py)：市场标签审计
- [scripts/posthoc_calibration_pack.py](./scripts/posthoc_calibration_pack.py)：冷启动 posthoc pack 构建器

## 下一步

- 给短句命令式中文补更严格的误判测试
- 给常见 Agent Runtime 补宿主适配器
- 补完整的 demo payload 和安装演示
- 把特化校准从中英文扩到更多语言

## License

ClawHub 发布包遵循平台统一的 `MIT-0` 条款。

GitHub 仓库继续以 [LICENSE](./LICENSE) 文件为准。
