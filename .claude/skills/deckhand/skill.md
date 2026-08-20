---
name: deckhand
description: |
  初始化项目的语义化发版流水线（当前基于 release-please）。
  自动生成 GitHub Actions workflow、release-please 配置文件和版本清单，
  引导你完成 GitHub 权限设置，然后推送配置分支。
  当用户说"配置自动发版"、"初始化 release-please"、"setup CI release"时使用此 skill。
---

# DeckHand Skill

自动为 git 仓库配置语义化发版流水线。当前后端：release-please。

---

## 执行流程

### 第一步：环境检查

1. 用 Bash 确认当前目录是 git 仓库
2. 用 `get_current_version()` 获取最新 tag 版本号
3. 用 `get_repo_name()` 获取仓库名

如果 `get_current_version()` 返回 None，版本号用 `0.0.0`。

### 第二步：生成配置文件

在 deckhand 项目根目录下运行 Python：

```bash
cd <deckhand项目路径>/src
python -c "
from deckhand.backends import get_backend
from deckhand.config import DeckHandConfig
from pathlib import Path

config = DeckHandConfig(
    backend='release-please',
    package_name='<仓库名>',
    current_version='<版本号>',
    changelog_path='CHANGELOG.md',
)

backend = get_backend('release-please')
files = backend.generate(config)

for filepath, content in files.items():
    target = Path('<目标仓库根目录>') / filepath
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    print(f'已生成: {filepath}')
"
```

或者直接在 Python 中 import 并执行。

生成的文件：
- `.github/workflows/release-please.yml`
- `release-please-config.json`
- `.release-please-manifest.json`

### 第三步：提交并推送

```bash
cd <目标仓库根目录>
git checkout -b chore/init-ci
git add .
git commit -m "chore: bootstrap release-please configuration"
git push --set-upstream origin chore/init-ci
```

### 第四步：引导 GitHub 权限设置（必须停下来）

告诉用户：

> 请在 GitHub 仓库页面完成以下操作：
> 1. Settings → Actions → General
> 2. Workflow permissions 选择 "Read and write permissions"
> 3. 勾选 "Allow GitHub Actions to create and approve pull requests"
> 4. 点击 Save

**不要跳过这一步。** 不做这个设置，release-please 无法自动创建 PR。

### 第五步：合并配置分支

告诉用户：

> 请在 GitHub 上将 `chore/init-ci` 合并进 `main`。

### 第六步：触发第一次发版

告诉用户：

> 现在机器人已安装但处于待机状态。需要进行一次功能提交来触发它：
>
> ```bash
> git checkout main && git pull
> git checkout -b feature/test-auto-release
> touch TRIGGER_RELEASE.md
> git add TRIGGER_RELEASE.md
> git commit -m "feat: trigger first automated release"
> git push --set-upstream origin feature/test-auto-release
> ```
>
> 然后在 GitHub 上创建 PR，点击 **Squash and merge** 合并。

合并后，机器人会自动创建 Release PR。

### 第七步：验证

引导用户检查：
1. Actions 页面确认 `release-please` workflow 成功
2. Pull Requests 页面确认机器人创建了 Release PR
3. 合并 Release PR 后检查 Releases 页面和 CHANGELOG.md

---

## 提交规范速查

| 效果 | PR 标题前缀 | 版本变化 |
|------|------------|---------|
| 新功能 | `feat: ...` | Minor (0.5.3 → 0.6.0) |
| 修 Bug | `fix: ...` | Patch (0.2.0 → 0.2.1) |
| 破坏性更新 | `feat!: ...` 或正文含 `BREAKING CHANGE:` | Major (0.2.0 → 1.0.0) |
| 不发版 | `chore:`, `docs:`, `refactor:`, `test:` | 无变化 |

---

## 注意事项

- 必须在 `chore/init-ci` 分支上操作，不要直接在 main 上
- 第四步的 GitHub 权限设置不可跳过
- 触发发版时必须使用 `feat:` / `fix:` / `feat!:` 前缀的 PR 标题
- 合并 Release PR 时使用 Squash and merge
