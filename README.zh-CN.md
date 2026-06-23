# 情绪.skill / Emotion Skill

[English](./README.md) · [GitHub](https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill) · `clawhub install emotion-skill`

给高压 Coding Agent 场景使用的 Markdown-first 技能。

这个 skill 的重点不是运行 Python 情绪分类器，而是给 agent 一套人和模型都能读懂的说明书：用户反复说没修好、要求依据、保护范围、等待无反馈、路径困惑或准备收口时，agent 应该如何路由、如何回复、如何验证、如何停止扩 scope。

## 为什么值得装

Coding Agent 常在这些时刻掉质量：

- 用户说同一个 bug 还在，Agent 继续解释。
- 用户要依据，Agent 继续猜。
- 用户要求只改一个文件，Agent 顺手动旁边配置。
- 工具或队列静默很久，Agent 没给进度。
- 用户说已经好了，Agent 又开新改动。

这个 skill 把这些场景转成可读的 routing 和 response 规则。

## 结构

ClawHub 发布包：

- `SKILL.md`：触发说明、主流程和 reference 索引
- `agents/openai.yaml`：界面元数据和默认调用提示
- `references/routing-playbook.md`：主路由、状态模式和冲突优先级
- `references/response-constraints.md`：依据优先、范围保护、进度、收口门禁
- `references/real-scenarios.md`：真实场景族，用于避免一例一修
- `references/model-prompts.md`：宿主需要时可用的紧凑 prompt overlay
- `references/integration-openclaw-hermes.md`：OpenClaw/Hermes 接入说明
- `references/examples.md`：前后对比示例
- `references/emotion-value-model.md`：价值和评估口径

GitHub 仓库额外保留：

- `scripts/`：回归、审计、真实场景和历史 runtime 验证工具
- `assets/`：校准和长尾案例材料
- `demo/`：本地 legacy runtime 检查样例
- 不进入安装包的研究和历史 reference

## 使用方式

在支持 skills 的 agent 中：

```text
Use $emotion-skill when the user asks for evidence, repeats a failed bug,
protects scope, waits through a delay, is confused by a path, or asks to close
out after success.
```

Agent 应先读 `SKILL.md`，再只加载匹配当前场景的 reference。不应要求用户或 agent 先运行 Python 分类器。

## 验证

仓库验证：

```bash
python scripts/markdown_skill_audit.py
python scripts/real_scenario_replay.py
python scripts/bundle_manifest_check.py
python scripts/marketplace_tag_audit.py
python scripts/alignment_test.py
python scripts/ablation_test.py
python scripts/smoke_test.py --seed 20260424 --strict
python -m compileall -q scripts
git diff --check
```

验证口径：

- Markdown audit 检查路由、披露和发布边界是否已经回到 Markdown-first。
- 真实场景 replay 检查场景族覆盖，不围绕单个句子打补丁。
- bundle manifest 确认 ClawHub 只发布精简 Markdown skill。
- legacy runtime 测试保留为回归证据，确保脚本退出安装路径时没有被误伤。

## 边界

这是 skill，不是 plugin。宿主可以基于这些 reference 做自动化，但安装后的 skill 本身应保持为人和 agent 都能直接阅读、直接执行的 Markdown 说明书。

## License

MIT. See the [GitHub repository license](https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill/blob/main/LICENSE).
