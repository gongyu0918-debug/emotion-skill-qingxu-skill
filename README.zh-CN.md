# 情绪.skill / Emotion Skill

[English README](./README.md)

Emotion Skill 是给 Coding Agent 用的一层轻量路由器。它读取最新用户消息、可选历史、运行时压力和本地画像，然后输出这一轮 Agent 应该怎么工作的指令。

它会把“还没修好”“先给依据”“别碰配置”“现在可以了，开始收口”这类信号，转成线程优先级、验证强度、回复风格、进度更新节奏和成功后守护策略。

## 它改变什么体验

| 用户状态 | Agent 行为 |
|---|---|
| 着急或被阻塞 | 留在主线程，更频繁更新进度，先做有效动作 |
| 重复失败后烦躁 | 先修复，再解释，提高验证强度 |
| 怀疑或要证据 | 先给依据、校验点和失败路径，再继续改 |
| 担心越界 | 先验证，收紧修改范围，保护文件和配置 |
| 看不懂路径 | 解释下一步，最多问一个澄清问题 |
| 已经成功 | 进入收口和防回归模式 |

## 30 秒试跑

先跑轻量 host 输出：

```bash
python scripts/emotion_engine.py host --message "这个问题还没修好，先给我依据，再继续改。" --pretty
```

你会看到这种结构：

```json
{
  "mode": "skeptical",
  "labels": ["frustrated", "skeptical"],
  "overlay_prompt": "<state mode=skeptical ...>",
  "routing": {
    "reply_style": "evidence_then_act",
    "verification_level": "high",
    "queue_mode": "collect",
    "prefer_main_thread": true,
    "progress_update_interval_sec": 20
  },
  "memory": {
    "should_persist": false
  }
}
```

再跑仓库自带的本地历史事件：

```bash
python scripts/emotion_engine.py host --input demo/local_history_event.json --pretty
```

用宿主适配器做只读预览：

```bash
python scripts/minimal_host_adapter.py --event demo/local_history_event.json --store-dir .demo-store --view host --no-persist --pretty
```

## 接入方式

先接这些字段：

- `overlay_prompt`：插入当前 Agent turn，作为紧凑状态提示。
- `routing.reply_style`：决定回复姿态，比如 `repair_then_explain`、`evidence_then_act`、`verify_then_act`。
- `routing.verification_level`：决定动手前要做多少验证。
- `routing.queue_mode`：决定继续收集、引导主任务，还是打断当前队列。
- `routing.progress_update_interval_sec`：决定进度更新间隔。
- `memory.should_persist`：决定宿主是否合并本轮画像更新建议。

最小事件：

```json
{
  "message": "这个问题还没修好，先给我依据，再继续改。",
  "history": [
    {"role": "assistant", "text": "我觉得已经定位到根因了。"}
  ],
  "runtime": {
    "response_delay_seconds": 20,
    "unresolved_turns": 3,
    "bug_retries": 2,
    "same_issue_mentions": 2
  }
}
```

完整契约和高级字段放在 [SKILL.md](./SKILL.md)。

## 无感使用边界

核心引擎是无状态的。它只返回 JSON。

最小宿主适配器在你启用跨轮自适应时，会写入三个宿主管理的 JSON 文件：

- `user_profile.json`
- `last_state.json`
- `calibration_state.json`

先用 `--no-persist` 做只读预览。真实接入时用 `--view host` 拿轻量输出。

## 安装

环境要求：

- Python `3.9+`
- 只用标准库

拉仓库：

```bash
git clone https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill.git
cd emotion-skill-qingxu-skill
```

按 Codex 风格作为本地 skill 使用。

macOS / Linux：

```bash
cp -r . ~/.codex/skills/emotion-skill
```

PowerShell：

```powershell
Copy-Item -LiteralPath . -Destination $HOME\.codex\skills\emotion-skill -Recurse -Force
```

## 输出模型

轻量 `host` 输出优先看这些字段：

- `state.emotion_vector.confusion`：用户侧的不确定感。
- `state.interaction_state.clarity`：从任务表述和上下文推断出的清晰度。
- `labels`：这一轮同时存在的状态。
- `mode`：这一轮真正驱动路由的主状态。

完整 `run` 输出把同一组值放在 `confirmed_state.*` 下，并附带诊断、提示词、特征信号和 review plans。

## 当前检查

当前本地检查结果：

- alignment regression：`70/70`
- curated ablation harness：`333/333`
- 同一套评分下的静态基线：`18/333`
- 随机社区烟测：`24/24 strict`，另外 5 轮 `12/12 strict`
- 独立审计：`ok`
- ClawHub 标签审计：`ok`
- feature gate 审计：`ok`

这些数字来自仓库内置回归集，适合用来抓行为漂移。

## 仓库结构

运行时相关：

- [SKILL.md](./SKILL.md)：skill 定义和完整契约
- [scripts/emotion_engine.py](./scripts/emotion_engine.py)：运行时引擎和 CLI
- [scripts/minimal_host_adapter.py](./scripts/minimal_host_adapter.py)：支持本地画像持久化的最小宿主适配器
- [demo/local_history_event.json](./demo/local_history_event.json)：真实本地历史 demo 事件
- [references/examples.md](./references/examples.md)：案例输入输出

评测和审计：

- [scripts/alignment_test.py](./scripts/alignment_test.py)：精选回归样例
- [scripts/ablation_test.py](./scripts/ablation_test.py)：skill 与静态基线对比
- [scripts/smoke_test.py](./scripts/smoke_test.py)：场景和社区烟测
- [scripts/independent_audit.py](./scripts/independent_audit.py)：契约与宿主边界审计
- [scripts/marketplace_tag_audit.py](./scripts/marketplace_tag_audit.py)：市场标签审计
- [scripts/posthoc_calibration_pack.py](./scripts/posthoc_calibration_pack.py)：posthoc pack 构建器

ClawHub 发布包带运行时子集。GitHub 保留完整评测面。

## License

ClawHub 发布包遵循平台统一的 `MIT-0` 条款。

GitHub 仓库继续以 [LICENSE](./LICENSE) 文件为准。
