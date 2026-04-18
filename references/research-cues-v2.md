# 情绪线索资料补充 v2

这份笔记只做一件事：把新增特征和它们的资料依据对齐。

## 1. 响应延迟和卡顿

- [Chronemic urgency in everyday digital communication](https://journals.sagepub.com/doi/10.1177/0961463X20987721)
  - 支持把响应时间理解成社会规范的一部分。
  - 对应到引擎里的 `delay_pressure`、`effective_delay_budget_seconds`、`same_issue_mentions`。
- [Opposing Effects of Response Time in Human–Chatbot Interaction](https://link.springer.com/article/10.1007/s12599-022-00755-x)
  - 支持把延迟作为直接影响用户感知的线索。
  - 对应到 `prefer_main_thread`、`progress_update_interval_sec`、`semantic_pass`。

## 2. 文本副语言和标点

- [Paralanguage Classifier (PARA)](https://journals.sagepub.com/doi/10.1177/00222437221116058)
  - 支持把标点、重复字符、字形变化当成可编码的文本副语言。
  - 对应到 `punctuation_pressure`、`dismissive_pressure`、`tempo_pause_pressure`。
- [Texting insincerely: The role of the period in text messaging](https://www.sciencedirect.com/science/article/abs/pii/S0747563215302181)
  - 支持句号和短促结尾会改变读者感知。
  - 对应到 `ABRUPT_EN_PATTERN`、`ABRUPT_ZH_PATTERN`。
- [Read. This. Slowly.](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2025.1410698/full)
  - 支持节奏化停顿和书写中的 pause 线索会改变情绪理解。
  - 对应到 `SPACED_DOTS_PATTERN`、`DOUBLE_DOT_PATTERN`、`tempo_pause_ratio`。

## 3. 非标准拼写、故意拼错、textisms

- [E-Leadership or “How to Be Boss in Instant Messaging?” The Role of Nonverbal Communication](https://journals.sagepub.com/doi/10.1177/2329488416685068)
  - 直接把 nonstandard spelling、letter repetition、orthography / typography 变化整理成数字沟通线索。
  - 对应到 `TEXTISM_TERMS`、`NONSTANDARD_SPELLING_TERMS`、`LATIN_ELONGATION_PATTERN`。
- [The Linguistic and Situational Features of WhatsApp Messages Among High School and University Canadian Students](https://journals.sagepub.com/doi/10.1177/21582440221082124)
  - 支持缩写、非标准标点、非标准大小写在真实消息里广泛存在，而且强依赖语境。
  - 对应到 `CASE_SHIFT_PATTERN`、`textism_ratio`、`surface_uncertainty`。
- [Spelling Errors in Brief Computer-Mediated Texts Implicitly Lead to Linearly Additive Penalties in Trustworthiness](https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2022.873844/full)
  - 支持拼写错误会影响读者的信任感知。
  - 对应到 `dismissive_pressure` 和 `trust` 里的小幅扣分。

## 4. 置信度和校准

- [Uncertainty Quantification and Confidence Calibration in Large Language Models: A Survey](https://arxiv.org/abs/2503.15850)
  - 支持把不确定性单独建模，而不是直接把每个弱线索都当成高置信信号。
  - 对应到 `surface_signal_reliability`、`surface_uncertainty`、`posthoc_weight`。

## 5. 社交媒体和定时任务语料

- [r/ios: Reminders app is not reminding me. Not getting notifications, tried everything.](https://www.reddit.com/r/ios/comments/1ihxvao/reminders_app_is_not_reminding_me_not_getting/)
  - 提供了“提醒没来”“该提醒的时候没提醒”“晚到就等于没到”这类时间失败话术。
  - 对应到 `MISSED_EXPECTATION_TERMS`。
- [r/SaaS: My automated background jobs silently broke for 3 days and nobody noticed, including me](https://www.reddit.com/r/SaaS/comments/1sb8esi/my_automated_background_jobs_silently_broke_for_3/)
  - 提供了“静默失败”“没人注意到”“没有告警”的公共抱怨模式。
  - 对应到 `MISSED_EXPECTATION_TERMS` 和社区校准集里的 silent-failure 样本。
- [r/sysadmin: How do you catch "zombie" cron jobs that hang but don't fail?](https://www.reddit.com/r/sysadmin/comments/1n4qcld/how_do_you_catch_zombie_cron_jobs_that_hang_but_dont_fail/)
  - 提供了“挂住但没失败”“跑很久没告警”“被监控盲掉”的运维型情绪表达。
  - 对应到 `stall_ratio`、`missed_expectation_ratio`、`skeptical` 路由提升。
- [tasks/tasks #603: Task reminder notifications are shown late on Android O](https://github.com/tasks/tasks/issues/603)
  - 提供了“提醒晚到”“晚了就是没用”的任务提醒区表达。
  - 对应到定时任务和提醒类共性样本。
- [taskforcesh/bullmq #3272: JobScheduler sometimes stops producing jobs](https://github.com/taskforcesh/bullmq/issues/3272)
  - 提供了“看起来还在跑，实际上已经静默停产”“drained 之后直接安静下来”的调度区表达。
  - 对应到 `MISSED_EXPECTATION_TERMS`、`stall_ratio` 和调度静默失败样本。
- [r/openclaw: Gateway silently dies: pattern report after 25 days of heavy use](https://www.reddit.com/r/openclaw/comments/1rfn0kz/gateway_silently_dies_pattern_report_after_25/)
  - 提供了“状态显示 running，但什么都不工作”“cron 卡住、消息不送达、没有告警”的社区抱怨模式。
  - 对应到矛盾状态、静默失败、主线程提权样本。
- [r/SideProject: I built a CLI that audits whether AI coding tools actually know your repo's rules](https://www.reddit.com/r/SideProject/comments/1smhsv9/i_built_a_cli_that_audits_whether_ai_coding_tools/)
  - 提供了“工具靠猜 CI 规则”“本地能过，CI 里炸”的 repo-grounding / guesswork 表达。
  - 对应到 `SPECULATION_TERMS` 和 `skeptical` 主导态校准。
- [r/googleassistant: Google Tasks not Working Properly With Reminders](https://www.reddit.com/r/googleassistant/comments/1c0dck1/google_tasks_not_working_properly_with_reminders/)
  - 提供了“没有提醒”“手动打开才突然出现”“重要事情直接错过”的提醒失败表达。
  - 对应到 `MISSED_EXPECTATION_TERMS`、提醒延迟和静默失败样本。
- [r/SideProject: I built a simple cron job monitor after one too many silent failures](https://www.reddit.com/r/SideProject/comments/1sm5rpm/i_built_a_simple_cron_job_monitor_after_one_too/)
  - 评论区补充了“expected interval + grace period”“runtime drift”“只从缺失的 side effect 才知道失败”的监控语言。
  - 对应到 `effective_delay_budget_seconds`、`task_age_minutes` 和任务超时窗口建模。
- [r/openclaw: Solving context loss after compaction/reset](https://www.reddit.com/r/openclaw/comments/1r3501p/solving_context_loss_after_compactionreset_a/)
  - 提供了“compaction 后对话线程消失”“像新会话一样重新开始”的上下文丢失表达。
  - 对应到 `CONTEXT_LOSS_TERMS`。
- [openai/codex #5957: Auto compaction causes GPT-5-Codex to lose the plot](https://github.com/openai/codex/issues/5957)
  - 提供了“忘记刚做过的编辑”“把当前动作错归到 previous sessions”“自信否认本轮事实”的上下文丢失 + 强质疑表达。
  - 对应到 `CONTEXT_LOSS_TERMS` 和高验证路由。
- [r/openclaw: Heartbeat broken? I used Cron instead](https://www.reddit.com/r/openclaw/comments/1s1s390/heartbeat_broken_i_used_cron_instead/)
  - 提供了“heartbeat 不执行”“忽略 isolatedSession / lightContext 参数”的自动化链路表达。
  - 对应到 `EXECUTION_PLUMBING_TERMS`。
- [openclaw/openclaw #45311: Slack socket mode connects but receives zero inbound events](https://github.com/openclaw/openclaw/issues/45311)
  - 提供了“connected, then silence”“zero inbound events”“stale-socket restarts do nothing”的执行空转表达。
  - 对应到 `EXECUTION_PLUMBING_TERMS` 和强质疑路由。
- [r/openclaw: Paperclip + OpenClaw gateway lose project context](https://www.reddit.com/r/openclaw/comments/1rz9sr8/anyone_else_seeing_paperclip_openclaw_gateway/)
  - 提供了“fallback workspace”“projectId = null”“workspaceId = null”“context plumbing”的上下文传递失败表达。
  - 对应到 `CONTEXT_LOSS_TERMS` 和 repo/handoff 校准。
- [r/hermesagent: Hermes Agent won't remember my rules](https://www.reddit.com/r/hermesagent/comments/1skesdm/hermes_agent_wont_remember_my_rules_how_are/)
  - 提供了“works within a session, forgets on the next session”的规则持久性表达。
  - 对应到 `CONTEXT_LOSS_TERMS`。
- [r/hermesagent: Anyone have hindsight working?](https://www.reddit.com/r/hermesagent/comments/1sf4y9b/anyone_have_hindsight_working/)
  - 提供了“feature is available but first prompt hangs for hours”的工具链空转表达。
  - 对应到 `EXECUTION_PLUMBING_TERMS` 和 `frustrated` 路由。
- [anthropics/claude-code #10838: systematically doubts user reports and defends its own code errors](https://github.com/anthropics/claude-code/issues/10838)
  - 提供了“我已经给了截图和证据”“停止怀疑用户报告”“先检查你自己的代码”这一簇证据导向质疑表达。
  - 对应到 `SKEPTICISM_TERMS`、`SPECULATION_TERMS` 和 `evidence_then_act` 路由。
- [r/hermesagent: Solving Token Bloat & Context Creep](https://www.reddit.com/r/hermesagent/comments/1siv7s0/master_thread_solving_token_bloat_context_creep/)
  - 提供了“14k token tax”“double injection”“disable unused tools”的上下文膨胀表达。
  - 当前作为候选词簇 `token_bloat_context_creep` 的社区依据，先不进运行时核心。

## 6. 设计结论

- 非标准标点、故意拼错、textisms、节奏化停顿都保留。
- 这些线索默认是低置信表层线索。
- 它们和延迟、卡住、反复失败、冲突、重复强调共振时，才会明显抬升 `urgent`、`frustrated`、`skeptical`。
- 冷启动阶段继续优先信后置拆解，成熟阶段再逐步抬高前置采信度。
