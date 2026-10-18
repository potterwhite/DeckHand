# DeckHand

[English](README.md) | [中文](README.zh-CN.md)

**甲板水手 —— 干那些重复、枯燥、但必不可少的活。**

这个仓库是一个 Claude Code **plugin marketplace**。每个 plugin 是一个独立单元，
自带 README 和技能，彼此无关，各装各的。

**该看哪一节：**

| 你想做什么 | 看 |
|---|---|
| 装上开始用 | 1 → 2 → 3 |
| 升级到最新版 | 4 |
| 改这个仓库里的 skill | 附录 1 |
| 加一个新 plugin | 附录 2 |

---

## 1. Plugins（有哪些）

| Plugin | 作用 | 文档 |
|---|---|---|
| `core` | 共享原语（标准库）—— 装一次，所有 workflow 受益 | [README](plugins/core/README.zh-CN.md) |
| `release-please` | 为任意 GitHub 仓库配置语义化自动发版流水线 | [README](plugins/release-please/README.zh-CN.md) |
| `appimage` | 把 .AppImage 装成桌面一等公民（`/opt`、图标、`.desktop`、URL scheme） | [README](plugins/appimage/README.zh-CN.md) |

## 2. 安装

两条命令，都得跑。`marketplace add` 只是把 catalog 拉下来，**它自己装不了任何东西**：

```
/plugin marketplace add potterwhite/DeckHand
/plugin install release-please@deckhand
```

照抄，别改。这两个标识符是不同的字符串，不能互换：

| 参数 | 来自 | 大小写 |
|---|---|---|
| `potterwhite/DeckHand` | GitHub repo 路径 | 原样 —— `DeckHand`，两个大写 |
| `release-please@deckhand` | `.claude-plugin/marketplace.json` 里的 `name` | 全小写 |

任一个大小写抄错，命令就会失败。

装完如果提示 `Run /reload-plugins to activate.`，跑一下 `/reload-plugins`。

## 3. 使用

技能带 plugin 名前缀调用：

```
/release-please:setup
```

plugin skill **不出现在** `/skills` 里 —— 这是设计如此，不是坏了。
用 `/plugin` 查看已装的东西和加载错误。

## 4. 更新

你机器上是这个仓库的一份 git clone，停在某个 commit。这里推了新 commit **不会**自动到你那边，得手动拉：

```
/plugin marketplace update deckhand
```

---

以下内容只有要改这个仓库的人才需要看。

## 附录 1 · 本地开发

marketplace 安装加载的是**钉在已推送 commit 上的缓存快照**，不是你的工作区 —— 所以改
`SKILL.md` 看起来毫无反应。直接挂载工作区：

```bash
claude --plugin-dir ./plugins/release-please    # 本会话内本地优先
/reload-plugins                                  # 每次改完
claude plugin validate ./plugins/release-please  # 提交前
```

完整步骤和那些会被误判成 bug 的现象：`/plugin-dev`。

## 附录 2 · 新增或修改 plugin

关于贡献的一切 —— 两层模型（workflow 与 `core`）、命名约定、准入标准、plugin 骨架、
每条 SKILL.md 必须嵌入的运行纪律母版区块、设计取向 —— 都在 **[CHARTER.md](CHARTER.md)**，
那是唯一权威来源。本 README 刻意不复述。

两条即使是使用者也值得知道的机制：

- plugin 安装时会把目录复制进缓存，所以 plugin 之间**不能**用 `../` 相对路径共享文件
  —— 每个单元必须自包含。
- 推送到 `main` 本身不会到达用户；改动随 plugin 的 `version` bump 才发布
  （见 CHARTER.md § Versioning）。

## License

MIT
