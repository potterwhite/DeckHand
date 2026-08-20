# DeckHand

**CI 自动化的甲板水手 —— 负责那些重复的、枯燥的、但必不可少的活。**

自动配置语义化发版流水线。目前基于 [release-please](https://github.com/googleapis/release-please)；
设计上支持任何发版自动化工具作为后端。

---

## 快速开始

```bash
pip install deckhand
cd 你的项目目录
deckhand setup
```

---

## 理念

船长需要甲板水手：处理重复、细节导向的工作，让船长专注于航行。
DeckHand 对你的 CI 流水线做同样的事 —— 无聊的初始化、样板配置、例行杂务 ——
让你专注于构建。

## 当前范围

- 从 git tag 检测当前版本号
- 生成 `.github/workflows/release-please.yml`
- 生成 `release-please-config.json`
- 生成 `.release-please-manifest.json`
- 自动 commit、push，并引导你完成 GitHub 权限设置

## 演进方向

- 可插拔后端（release-please、semantic-release、changesets、自定义）
- 独立 CLI 工具（`deckhand setup`、`deckhand ship`、`deckhand status`）
- MCP Server，供 AI 工具调用
- Docker 镜像，适配 CI 环境

## 状态

早期脚手架。Skill 版已在 Claude Code 中可用；独立 CLI 是下一步。

---

## 项目结构

```
deckhand/
├── .claude/skills/deckhand/skill.md   ← Claude Code Skill 编排脚本
├── src/deckhand/
│   ├── __init__.py                    ← 版本号
│   ├── cli.py                         ← CLI 入口 (setup / status / ship)
│   ├── config.py                      ← DeckHandConfig 配置类
│   ├── git.py                         ← git 工具函数 (版本检测, 仓库名等)
│   └── backends/
│       ├── __init__.py                ← 后端注册表
│       ├── base.py                    ← Backend 抽象基类
│       └── release_please.py          ← release-please 实现
├── config/                            ← 运行时配置 (未来用)
├── docs/                              ← 文档
└── pyproject.toml                     ← 项目配置
```

### 核心概念

```
Backend (抽象基类)
  ├── generate(config) → dict[str, str]   # 输入配置，输出文件内容
  │
  ├── ReleasePleaseBackend                # 当前唯一实现
  │     ├── _workflow()     → .github/workflows/release-please.yml
  │     ├── _config()       → release-please-config.json
  │     └── _manifest()     → .release-please-manifest.json
  │
  └── (未来) SemanticReleaseBackend
        └── ChangesetsBackend
```

### 数据流

```
用户输入 (package_name, changelog_path 等)
        ↓
DeckHandConfig
        ↓
Backend.generate(config) → {文件路径: 文件内容}
        ↓
写入目标仓库 → git commit → git push
```

---

## 安装

```bash
pip install deckhand
```

开发模式：

```bash
git clone https://github.com/potterwhite/DeckHand.git
cd DeckHand
pip install -e .
```

---

## 用法

```bash
# 初始化 release-please 配置
deckhand setup

# 检查当前仓库的发版配置状态
deckhand status

# 触发发版流程（未来支持）
deckhand ship
```

### 在 Python 中使用

```python
from deckhand.backends import get_backend
from deckhand.config import DeckHandConfig
from pathlib import Path

config = DeckHandConfig(
    backend="release-please",
    package_name="my-project",
    current_version="0.1.0",
    changelog_path="CHANGELOG.md",
)

backend = get_backend("release-please")
files = backend.generate(config)

for filepath, content in files.items():
    target = Path.cwd() / filepath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
```

---

## 协议

MIT
