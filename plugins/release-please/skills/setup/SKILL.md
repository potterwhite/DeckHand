---
name: setup
description: 为 git 仓库配置 release-please 自动发版流水线：侦察仓库特征、生成 GitHub Actions workflow、引导完成必需的仓库权限设置、验证首次运行。当用户要求"配置自动发版"、"初始化 release-please"、"setup CI release"、"加自动 changelog"时使用。
allowed-tools: Read, Glob, Bash(git rev-parse *), Bash(git remote *), Bash(git tag *), Bash(git log *), Bash(git status *), Bash(git branch *), Bash(gh repo view *), Bash(gh auth status)
---

# release-please setup

在**目标仓库**（用户当前所在的仓库，不是 DeckHand 自己）配置自动发版。

## 铁律

1. 推送前、改仓库设置前，停下来让用户确认。
2. 已存在的 `.github/workflows/release*.yml` 或 `CHANGELOG.md` 绝不静默覆盖 —— 报告并询问。
3. remote 不是 GitHub 就停止：release-please-action 只跑在 GitHub。

## 步骤 1 · 侦察

```bash
git remote get-url origin                                 # 是否 GitHub、owner/repo
git remote show origin | sed -n 's/.*HEAD branch: //p'    # 默认分支
git tag --sort=-v:refname | head -5                       # 现有版本、tag 前缀
ls .github/workflows/ CHANGELOG.md 2>/dev/null            # 冲突物
gh repo view --json viewerPermission -q .viewerPermission # 是否 ADMIN，决定步骤 4 走哪条路
gh auth status 2>&1 | grep -i 'token scopes'              # 仅当 remote 是 https:// 时才需要看
```

**别用 `git symbolic-ref refs/remotes/origin/HEAD` 取默认分支** —— 这个 ref 在很多仓库里
根本没设置，会直接报 `fatal: ref ... is not a symbolic ref`。用上面那条 `git remote show`，
或 `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`。

**remote 是 `https://` 且 token scopes 里没有 `workflow`，现在就停下告诉用户。** 本 skill 唯一
的产出就是 `.github/workflows/` 下的文件，而 GitHub 禁止缺 `workflow` scope 的 OAuth token
写这个目录 —— 到步骤 3 push 时必然被拒。SSH remote 不受此限制。解法见
[references/gotchas.md](references/gotchas.md) 第 0 条。

按根目录的包清单决定 `release-type`：

| 检测到 | release-type |
|---|---|
| `package.json` | `node` |
| `pyproject.toml` / `setup.py` | `python` |
| `Cargo.toml` | `rust` |
| `go.mod` | `go` |
| `pom.xml` | `maven` |
| `composer.json` | `php` |
| `*.gemspec` | `ruby` |
| 都没有 | `simple` |

## 步骤 2 · 生成 workflow

读 `${CLAUDE_SKILL_DIR}/templates/release-please.yml`，替换 `__DEFAULT_BRANCH__`
和 `__RELEASE_TYPE__`，写到目标仓库的 `.github/workflows/release-please.yml`。

一个文件就够。遇到 monorepo、要钉死起始版本、要把版本号同步进源文件 ——
读 `${CLAUDE_SKILL_DIR}/references/gotchas.md`。

## 步骤 3 · 提交推送（停下确认）

新建分支提交并 push，不要直接推默认分支。

**`git push` 不要接管道。** `git push | tail` 的退出码是 `tail` 的，永远为 0，推失败会看起来
像成功。真被拒时读 `[remote rejected]` 那一行，别信旁边那段 `Note about fast-forwards` 的 hint。

## 步骤 4 · 开权限开关（停下确认）

**全流程唯一需要 repo admin 权限的动作。** 不做，release-please 就无法创建 PR。
这个开关无法用 workflow yaml 里的 `permissions:` 块代替。

有 `gh` 且已登录：

```bash
gh api -X PUT repos/OWNER/REPO/actions/permissions/workflow \
  -f default_workflow_permissions=write \
  -F can_approve_pull_request_reviews=true
```

否则把链接给用户，让他勾选 **Allow GitHub Actions to create and approve pull requests** 再 Save：

```
https://github.com/OWNER/REPO/settings/actions
```

## 步骤 5 · 合并后验证

合并配置分支到默认分支 → workflow 自动跑。

release-please 扫的是「上次 release 以来的提交」。历史里已有 `feat:`/`fix:` 就会立刻开
Release PR；**一条规范提交都没有时才需要补一个** —— 不要无脑造假 commit。

```bash
gh run list --workflow=release-please.yml --limit 3
gh pr list --label "autorelease: pending"
```

报错 `GitHub Actions is not permitted to create or approve pull requests`
就是步骤 4 没做。其他失败读 `${CLAUDE_SKILL_DIR}/references/gotchas.md`。

## 提交规范

`feat:` → minor，`fix:` → patch，`feat!:` 或正文含 `BREAKING CHANGE:` → major，
`chore:` / `docs:` / `refactor:` / `test:` → 不发版。

squash merge 时 release-please 读的是 **PR 标题**，所以 PR 标题必须合规。
