# Core Feature Admission v1

这份表只做一件事：限制运行时核心继续膨胀。

## 准入规则

一个新特征词簇进入运行时核心，要同时满足三条：

1. 有心理学或语言学支持
2. 有社区共性复现
3. 能稳定改善 `alignment + ablation + real-case routing`

旧特征也按这套规则回审。

## 当前做法

- 运行时核心只收主题词簇
- 语料和实验层放在 `assets/` 和 `scripts/`
- 其他语言只保留跨语言弱支持
- 候选词簇可以继续收集语料，但不会直接进入核心
- `feature_gate_audit.py` 会核对核心词簇是否挂到了 `alignment_test.py` 和 `ablation_test.py`

## 当前状态

核心词簇：

- `urgency_delay_burst`
- `frustration_repeat_loop`
- `skepticism_evidence`
- `skepticism_guesswork`
- `cautious_boundary`
- `satisfaction_guard`
- `dismissive_pause_surface`
- `typo_textism_rush`
- `silent_failure_timing`
- `context_loss_memory`
- `execution_plumbing_gap`

候选词簇：

- `token_bloat_context_creep`

## 为什么 `token_bloat_context_creep` 先留候选

这簇社区复现已经足够强，研究支持也足够。

当前还差最后一关：它还没有像 `silent_failure_timing` 或 `execution_plumbing_gap` 一样，稳定改变线程路由、验证强度或解释顺序。等它能明确改变工作模式，再进核心。

## 审计命令

```bash
python scripts/feature_gate_audit.py
```

它会检查所有 `core` 词簇是否都满足三条准入条件，并验证它们引用的 `alignment` / `ablation` 用例确实存在。
