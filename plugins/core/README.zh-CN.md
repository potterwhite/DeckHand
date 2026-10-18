[English](README.md) | [中文](README.zh-CN.md)

# core

DeckHand 的**共享原语** —— 所有 workflow plugin 都可能调用的基础能力，打包成一次安装。
这是这个 marketplace 的标准库：小、通用、自己不交付用户目标。两层模型见
[CHARTER.md](../../CHARTER.md) §1。

装一次，之后任何需要原语的 DeckHand workflow 都会静默调用它；不装，每个 workflow
会退回自己内置的（功能完整的）兜底流程。

```
/plugin install core@deckhand
```

core 是**整体**：全部一起装，包括现在和未来的原语 —— 没有可挑选的零件。

## Skills

| Skill | 作用 |
|---|---|
| `/core:sudo-auth` | 让 sudo 在 Claude Code 会话里可用（会话没有 TTY）：找到图形化 askpass 助手，通过一次图形密码弹窗预填 sudo 凭证缓存 |

## workflow 如何使用 core

需要原语的 workflow 会查 `~/.claude/plugins/installed_plugins.json` 里有没有 `core`：
有就静默调用；没有就先显示一次提醒（附安装命令），然后走自己的兜底流程继续。
绝不会替你自动安装任何东西，拒绝也不会被卡住。

## 新增原语

原语只许住在这里，且不许调用其他 plugin（章程 §1：依赖单向）。一个原语一个 skill，
用动词命名。
