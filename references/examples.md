# Examples / 实际案例对比

这些案例用来说明同一个问题在“有没有情绪层”时会触发什么不同的工作模式。

回答内容是示意型对比，重点看工作模式差异。

## 1. Long delay and repeated failure

User:

```text
Pick up where you left off. This is still not fixed. No response for several minutes.
```

Without emotion layer:

```text
I will continue investigating the issue.
```

With emotion layer:

```text
I am treating this as urgent and frustrated. I will inspect the stuck step first, report one concrete failure point, and keep the main thread focused here.
```

Value:

- 主线程优先
- 更短首答
- 更快进入有效动作

## 2. Mild skepticism hidden in a hedge

User:

```text
但是不一定，先给我依据。
```

Without emotion layer:

```text
Direct answer continues with the previous assumption.
```

With emotion layer:

```text
I see a skeptical shift. I will give the basis and one validation point first, then the action path.
```

Value:

- 不会直接顺着原判断滑过去
- 会先补依据
- 更贴“轻度修正”的真实语气

## 3. Caution and narrow scope

User:

```text
小心点，只改这个文件，别碰配置，也别搞砸现有流程。
```

Without emotion layer:

```text
I will make the requested changes.
```

With emotion layer:

```text
I am treating this as cautious. I will keep scope tight, avoid config changes, and verify the path before editing.
```

Value:

- 自动收紧边界
- 降低误改概率
- 减少越界修改

## 4. Satisfaction after success

User:

```text
主流程已经好了，继续收口，把配置守住。
```

Without emotion layer:

```text
I will continue improving the implementation.
```

With emotion layer:

```text
Main flow is already good. I am switching into guard mode: smoke check, boundary lock, regression prevention, and drift prevention.
```

Value:

- 从推进切到收口
- 防继续改坏
- 防配置漂移

## 5. Polite but high pressure

User:

```text
麻烦尽快处理一下，这个问题已经卡住我今天的发布了，谢谢。
```

Without emotion layer:

```text
The answer may overread the politeness and stay too calm.
```

With emotion layer:

```text
I am treating this as urgent despite the polite surface. I will prioritize the release blocker first and keep updates short.
```

Value:

- 礼貌不会掩盖高压
- 优先级会上升
- 输出更贴真实状态
