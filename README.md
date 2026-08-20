# DeckHand

**CI 自动化的甲板水手 —— 负责那些重复的、枯燥的、但必不可少的活。**

自动配置语义化发版流水线。目前基于 [release-please](https://github.com/googleapis/release-please)；
设计上支持任何发版自动化工具作为后端。

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
