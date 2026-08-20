# DeckHand

**甲板水手 —— 干那些重复、枯燥、但必不可少的活。**

这个仓库是一个 Claude Code **plugin marketplace**。每个 plugin 是一个独立单元，
自带 README 和技能，彼此无关，各装各的。

## Plugins

| Plugin | 作用 | 文档 |
|---|---|---|
| `release-please` | 为 GitHub 仓库配置语义化自动发版流水线 | [README](plugins/release-please/README.md) |

## 安装

```
/plugin marketplace add potterwhite/DeckHand
/plugin install release-please@deckhand
```

装完如果提示 `Run /reload-plugins to activate.`，跑一下 `/reload-plugins`。

技能带 plugin 名前缀调用，例如 `/release-please:setup`。

## 本地开发

改 plugin 时不用装，直接挂载：

```bash
claude --plugin-dir ./plugins/release-please
```

改完 `SKILL.md` 跑 `/reload-plugins` 生效，不用重启。

想让某个 plugin 在所有项目里常驻（软链接，改动即时生效）：

```bash
ln -s "$PWD/plugins/release-please" ~/.claude/skills/release-please
```

提交前验证结构：

```bash
claude plugin validate ./plugins/release-please
```

## 加一个新 plugin

hierarchy 已经定型，加东西只是 `mkdir`，不需要改动现有结构：

```bash
mkdir -p plugins/新名字/{.claude-plugin,skills/某技能}
```

然后写三个文件：

```
plugins/新名字/
├── .claude-plugin/plugin.json     # name / description / version
├── README.md                      # 这个单元自己的说明
└── skills/某技能/
    └── SKILL.md                   # frontmatter: name + description
```

最后在根目录 `.claude-plugin/marketplace.json` 的 `plugins` 数组里加一条
（`source` 是相对 `./plugins` 的路径，也就是目录名）。

## 结构

```
DeckHand/
├── .claude-plugin/marketplace.json   ← 仓库即 marketplace，列出所有 plugin
└── plugins/
    └── release-please/               ← 一个独立单元
        ├── .claude-plugin/plugin.json
        ├── README.md
        └── skills/setup/
            ├── SKILL.md
            ├── templates/            ← 静态模板，skill 复制并替换占位符
            └── references/           ← 按需加载的深度资料
```

**注意**：plugin 安装时是把目录复制到缓存，所以 plugin 之间**不能**用 `../` 相对路径
共享文件 —— 每个单元必须自包含。

## 设计取向

没有 Python，没有二进制，没有要安装的运行时。全部是 Markdown 指令加静态模板。

因为这类活的难点从来不是计算，而是判断：这是 monorepo 吗？tag 前缀是 `v` 还是裸的？
已有的 CHANGELOG 要保留还是接管？失败日志到底在说什么？特殊情况太多，
写成 if-elif 只会在真正有意思的仓库上出错。判断交给模型，确定性的部分交给静态模板。

## License

MIT
