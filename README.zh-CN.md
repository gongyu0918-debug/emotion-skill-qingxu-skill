# 情绪.skill / Emotion Skill

[English README](./README.md)

> 让 Agent 听懂空气，不只是听懂任务。

把用户的急切、质疑、困惑、谨慎、满意，从一句话里的词、标点、节奏、延迟和上下文变化里拎出来，直接改 Agent 的工作模式。

[安装](#安装) · [调用](#调用) · [它到底有什么用](#它到底有什么用) · [案例对比](#案例对比) · [思路链审查](#思路链审查)

---

## 这是什么

这是一个给 Coding Agent 用的情绪编排层。

它不负责替你写内容，它负责改工作方式：

- 什么时候抢主线程
- 什么时候先修再解释
- 什么时候先给依据
- 什么时候把 scope 收紧
- 什么时候别再乱改，直接进入收口和防漂移

目标很简单：让 AI 学会察言观色，读空气。

---

## 安装

### GitHub

```bash
git clone https://github.com/gongyu0918-debug/emotion-skill-qingxu-skill.git
cd emotion-skill-qingxu-skill
```

### 装进本地 skills

macOS / Linux:

```bash
cp -r emotion-skill-qingxu-skill ~/.codex/skills/emotion-skill
```

PowerShell:

```powershell
Copy-Item -LiteralPath .\emotion-skill-qingxu-skill -Destination $HOME\.codex\skills\emotion-skill -Recurse -Force
```

### 直接跑引擎

```bash
python scripts/emotion_engine.py run --input turn.json --pretty
```

### ClawHub

发布后可直接安装：

```bash
clawhub install emotion-skill
```

---

## 调用

### 无感调用

接到 `message_received` 或 `before_agent_start`，每轮自动跑。

用户正常说话就行，不需要专门喊技能名。

### 开箱即用

直接给 `emotion_engine.py` 一个 JSON 输入，拿走这两个输出：

- `overlay_prompt`
- `routing.thread_interface`

前者插进系统 prompt，后者接线程、队列、heartbeat 和子任务路由。

### 后台分析

每轮结束后再跑一次后置反问，专门拆这句话里的情绪词、姿态词、修正词和节奏线索。

它不打断用户，也不抢流式输出。

---

## 语言覆盖

当前特化校准只覆盖两条线：

- 中文
- 英文

这两种语言已经补了共性情绪表达、社区语料、标点习惯、节奏停顿、赶打错拼和 agent 使用场景里的抱怨模式。

其他语言当前只有弱支持，主要依赖：

- 通用标点强度
- 重复和停顿
- 延迟压力
- 多轮重复失败
- 命令式结构

仓库和发行说明会明确写这一点：当前版本没有对其他语言做专门特化训练。

---

## 它到底有什么用

最值钱的地方有五个：

| 状态 | Agent 会变什么 | 价值 |
|---|---|---|
| `urgent` | 抢主线程、压后 heartbeat、缩短进度更新 | 更快给出第一个有效动作 |
| `frustrated` | 先修再解释、提高验证强度 | 少说废话，先止损 |
| `skeptical` | 先给依据和校验点 | 少拍脑袋，少误诊 |
| `cautious` | 收紧 scope、优先安全路径 | 少越界修改，少误改 |
| `satisfied` | 进入 guard mode | 防配置漂移、防回归、防继续改坏 |

所以它真正改的不是语气，是这四件事：

1. 任务优先级
2. 验证强度
3. 解释方式
4. 成功后的收口动作

---

## 它怎么感知情绪

三层。

### 1. 前置筛选

看这些信号：

- 词汇
- 标点
- 长短
- 错别字和拼写错误
- 重复强调
- 长时间没响应
- 同一问题几轮没解决
- 和上文是否冲突

### 2. 后置反问

反问一句隐藏问题：

这句话里有没有情绪词、姿态词、修正词、节奏线索？

它重点抓弱信号，比如：

- `不一定`
- `应该`
- `吧`
- `你确定`
- `先给我依据`
- `Fine.`

### 3. 持久记忆

慢慢学这个用户的常态：

- 能忍多长延迟
- 说话有多短
- 爱不爱质疑
- 边界感强不强
- 喜不喜欢发散

---

## 动态权重

这套 skill 不是固定死的。

冷启动时，后置权重大，前置权重小。因为这时候用户画像还很薄。

后面看一个核心指标：

- `consistency_rate`

也就是前置和后置长期吻合率。

如果吻合率高，前置权重上升。
如果吻合率低，后置继续主导。

所以它天然就是因人而异的。

---

## 案例对比

完整案例在 [references/examples.md](./references/examples.md)。

### 案例 1：卡住很久

用户：

```text
Pick up where you left off. This is still not fixed. No response for several minutes.
```

没有情绪层：

```text
I will continue investigating the issue.
```

有情绪层：

```text
我把这轮当成高优先级处理。先定位卡住的步骤，再给你一个明确的失败点，然后才继续改。
```

### 案例 2：轻度质疑

用户：

```text
但是不一定，先给我依据。
```

没有情绪层：

```text
继续顺着原判断往下讲。
```

有情绪层：

```text
我先给判断依据和一个校验点，再给动作路径。
```

### 案例 3：已经好了，别乱动

用户：

```text
主流程已经好了，继续收口，把配置守住。
```

没有情绪层：

```text
继续泛化修改。
```

有情绪层：

```text
切到 guard mode：先做 smoke check、锁边界、防回归、防配置漂移。
```

---

## 思路链审查

这个项目的起点是一串连续的人类提示词。

架构设计和实现是在 AI 的帮助下完成的，但核心问题意识来自人：

- AI 没有情绪
- 人有情绪，而且经常自己都没意识到
- 这些情绪会影响人对“好回答”的期待
- 所以应该把情绪信号翻译成 Agent 的工作模式

我把这条思路链浓缩到了 [references/prompt-chain-audit.md](./references/prompt-chain-audit.md)。

里面已经显式整理成 `VIBE CODING 思维链条 / PROMPT 整理版`。

这份文档就是留给别人挑错的。你可以直接检查：

- 哪些心理学映射太粗
- 哪些语言学规则过拟合
- 哪些路由动作太重
- 哪些标签边界还不稳

---

## 当前状态

- 对齐回归：`26/26`
- 社区消融：`78.05%`
- 无情绪层基线：`4.88%`
- 后置校准社区样本：`56`

---

## 仓库结构

- [SKILL.md](./SKILL.md)：技能定义
- [scripts/emotion_engine.py](./scripts/emotion_engine.py)：运行时引擎
- [scripts/alignment_test.py](./scripts/alignment_test.py)：对齐回归
- [scripts/ablation_test.py](./scripts/ablation_test.py)：有无技能对比
- [scripts/posthoc_calibration_pack.py](./scripts/posthoc_calibration_pack.py)：后置校准样本包生成器
- [references/emotion-value-model.md](./references/emotion-value-model.md)：情绪层的价值模型

---

## 协议

MIT License。

公开、透明、方便审查，也方便别人拿去改。
