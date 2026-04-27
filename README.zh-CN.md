# 情绪.skill / Emotion Skill

[English README](./README.md)

Emotion Skill 是给 Coding Agent 用的轻量编排层。它读取最新用户消息、近期历史、运行时压力和可选本地画像，然后返回一份紧凑 JSON，告诉宿主这一轮 Agent 应该怎么工作。

它专门处理 Coding Agent 最容易失去信任的几个场景：重复失败、卡住无反馈、用户要求依据、担心越界、成功后的收口。

![Python](https://img.shields.io/badge/python-3.9%2B-3776AB)
![Dependencies](https://img.shields.io/badge/dependencies-standard%20library-2E7D32)
![License](https://img.shields.io/badge/license-MIT-blue)

## 为什么需要它

同一条 coding 任务，用户状态变了，Agent 的工作方式也要变。

| 用户信号 | 运行时行为 |
|---|---|
| “这个还没修好” | 留在主线程，提高验证强度，缩短进度更新间隔 |
| “先给我依据” | 先给证据、校验点和失败路径，再继续改 |
| “只改这个文件” | 收紧 scope，保护配置，先验证再动手 |
| “我看不懂” | 解释下一步，最多问一个澄清问题 |
| “已经好了，收口” | 进入 guard mode，做回归检查，防止继续漂移 |

输出保持朴素：宿主可消费的 JSON 字段，适合日志、路由和下一轮回复约束。

## 安装

```bash
git clone https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill.git
cd emotion-skill-qingxu-skill
python scripts/download_smoke.py
```

环境要求：

- Python `3.9+`
- 只用标准库

按 Codex 本地 skill 方式安装：

```bash
cp -r . ~/.codex/skills/emotion-skill
```

PowerShell：

```powershell
Copy-Item -LiteralPath . -Destination $HOME\.codex\skills\emotion-skill -Recurse -Force
```

## 30 秒试跑

```bash
python scripts/emotion_engine.py host --message "这个问题还没修好，先给我依据，再继续改。" --pretty
```

输出结构大致如下：

```json
{
  "mode": "skeptical",
  "labels": ["frustrated", "skeptical"],
  "route_reasons": ["repeat_failure_pressure", "evidence_requested"],
  "response_constraints": ["show_basis_first", "name_verification_steps"],
  "overlay_prompt": "<state mode=skeptical ...>",
  "routing": {
    "reply_style": "evidence_then_act",
    "verification_level": "high",
    "queue_mode": "collect",
    "prefer_main_thread": true
  },
  "satisfaction_lock": {
    "active": false
  }
}
```

跑仓库自带的本地历史事件：

```bash
python scripts/emotion_engine.py host --input demo/local_history_event.json --pretty
```

预览宿主侧持久化适配器，且不写入状态：

```bash
python scripts/minimal_host_adapter.py --event demo/local_history_event.json --store-dir .demo-store --view host --no-persist --pretty
```

## 宿主契约

真实接入优先使用 `host` 输出。它返回宿主最常用的字段：

- `overlay_prompt`：插入当前 turn 的小型状态提示。
- `mode`：本轮主导编排模式。
- `labels`：本轮同时存在的用户状态。
- `route_reasons`：可记录到日志的紧凑路由原因。
- `response_constraints`：下一轮回复的直接约束。
- `routing.reply_style`：回复姿态，例如 `repair_then_explain`、`evidence_then_act`、`verify_then_act`。
- `routing.verification_level`：动手前的检查强度。
- `routing.queue_mode`：继续收集、引导当前任务，或打断队列。
- `routing.progress_update_interval_sec`：进度更新节奏。
- `satisfaction_lock`：成功后收口和防回归策略。
- `state.state_delta`：相对宿主持有状态的显著变化。
- `memory.should_persist`：是否建议合并画像更新。

最小输入：

```json
{
  "message": "这个问题还没修好，先给我依据，再继续改。"
}
```

常用可选字段：

```json
{
  "message": "只改 parser 文件，先给失败路径。",
  "history": [
    {"role": "assistant", "text": "我觉得上一轮已经修好了。"}
  ],
  "runtime": {
    "response_delay_seconds": 20,
    "unresolved_turns": 3,
    "bug_retries": 2,
    "same_issue_mentions": 2
  },
  "last_state": {},
  "calibration_state": {},
  "user_profile": {}
}
```

顶层 payload 必须是 JSON object。JSON 格式错误、文件缺失、顶层数组都会返回退出码 `2` 和单行错误。

## 输出模式

| 命令 | 用途 |
|---|---|
| `host` | 真实宿主集成和紧凑输出 |
| `run` | 完整诊断、prompts、features、prediction 和 review plans |
| `screen` | 文本、历史和 runtime hint 的确定性初筛 |
| `confirm` | rule screen 与可选语义输入后的最终状态 |
| `route` | 只看路由 |
| `guide` | 只看短澄清建议 |
| `overlay` | 检查 overlay prompt |
| `posthoc` | review pass 和校准调试 |

## 持久化边界

核心引擎无状态。它返回 JSON，无网络调用；只有传入 `--output` 时才写文件。

最小宿主适配器会在 `--store-dir` 下维护三个宿主文件：

- `user_profile.json`
- `last_state.json`
- `calibration_state.json`

用 `--no-persist` 做只读预览。删除这三个文件即可重置本地自适应。store JSON 损坏时会指出具体路径；加 `--ignore-bad-store` 可以跳过坏 store 并从空状态继续。

## 语言覆盖

中文和英文有专门校准：共性情绪表达、社区语料、标点习惯、停顿、赶打错拼和 coding-agent 失败报告。

其他语言使用通用标点、重复、延迟和结构信号，输出适合作为弱路由提示。

## 验证

发布包冒烟：

```bash
python scripts/download_smoke.py
```

GitHub 全量验证：

```bash
python scripts/alignment_test.py
python scripts/ablation_test.py
python scripts/smoke_test.py --seed 20260424 --strict
python scripts/independent_audit.py
python scripts/marketplace_tag_audit.py
python scripts/feature_gate_audit.py
python scripts/bundle_manifest_check.py
```

2026-04-27 使用 Python 3.11.9 本地验证：

- alignment regression：`70/70`
- curated ablation harness：`333/333`
- 同一套评分下的静态基线：`18/333`
- strict smoke：`ok`
- independent audit：`ok`
- marketplace tag audit：`ok`
- feature gate audit：`ok`
- download smoke：`ok`
- bundle manifest check：`ok`

## 发布包内容

ClawHub 发布运行时子集：

- `SKILL.md`
- `README.md`
- `README.zh-CN.md`
- `CHANGELOG.md`
- `LICENSE`
- `agents/openai.yaml`
- `scripts/emotion_engine.py`
- `scripts/minimal_host_adapter.py`
- `scripts/download_smoke.py`
- `demo/local_history_event.json`
- `references/examples.md`
- `references/model-prompts.md`
- `references/emotion-value-model.md`
- `references/emotion-policy-matrix.md`
- `references/integration-openclaw-hermes.md`

GitHub 仓库保留完整回归、审计和校准文件。

## 集成文档

- OpenClaw / Hermes 接入：[references/integration-openclaw-hermes.md](./references/integration-openclaw-hermes.md)
- 行为案例：[references/examples.md](./references/examples.md)
- 策略矩阵：[references/emotion-policy-matrix.md](./references/emotion-policy-matrix.md)
- 价值模型：[references/emotion-value-model.md](./references/emotion-value-model.md)
- 模型提示词：[references/model-prompts.md](./references/model-prompts.md)

## License

MIT。见 [LICENSE](./LICENSE)。
