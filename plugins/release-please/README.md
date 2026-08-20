# release-please

为任意 GitHub 仓库配置 [google/release-please](https://github.com/googleapis/release-please)
语义化自动发版：提交用 `feat:` / `fix:` 前缀，机器人自动算版本号、写 CHANGELOG、开 Release PR、打 tag、发 Release。

## 技能

| 技能 | 作用 |
|---|---|
| `/release-please:setup` | 在当前仓库配置整套流水线 |

## 用法

在**目标仓库**里跑：

```
/release-please:setup
```

## 它会做什么

1. **侦察** —— 默认分支、现有 tag、语言生态、有无冲突的 workflow
2. **生成** —— 一个 `.github/workflows/release-please.yml`
3. **提交推送** —— 新建分支，停下来等你确认
4. **开权限开关** —— 全流程唯一需要 repo admin 的动作，停下来等你确认
5. **验证** —— 检查首次运行，解释失败原因

## 前置条件

| 需要 | 什么时候 | 没有的话 |
|---|---|---|
| `git` + push 权限 | 全程 | 无法进行 |
| GitHub remote | 全程 | 不支持（action 只跑在 GitHub） |
| repo admin 权限 | 步骤 4 | 得找有权限的人点一下 |
| `gh` 已登录 | 步骤 4、5 | 退化成给你链接自己点，功能不减 |

## 深入

`skills/setup/references/gotchas.md` —— monorepo、版本号钉死、pre-1.0 行为、
`extra-files` 同步版本、分支保护冲突、PAT 与下游 workflow 触发。
