[English](README.md) | [中文](README.zh-CN.md)

# release-please

为任意 GitHub 仓库配置 [google/release-please](https://github.com/googleapis/release-please)
语义化自动发版：提交用 `feat:` / `fix:` 前缀，机器人自动算版本号、写 `CHANGELOG.md`、开 Release PR、
打 tag、发 GitHub Release。

## 1. 技能

| 技能 | 作用 |
|---|---|
| `/release-please:setup` | 在当前仓库配置整套流水线 |

## 2. 用法

还没装？见[仓库根 README](../../README.zh-CN.md#2-安装)。

在**目标仓库**里跑：

```
/release-please:setup
```

## 3. 它会做什么

1. **侦察** —— 默认分支、现有 tag 与 release、语言生态、有无冲突文件
2. **商定版本策略** —— 停下来问你两个问题，见附录 1
3. **生成** —— 三个文件：workflow、`release-please-config.json`、`.release-please-manifest.json`
4. **提交推送** —— 新建分支，停下来等你确认
5. **开权限开关** —— 全流程唯一需要 repo admin 的动作，停下来等你确认
6. **验证** —— 检查首次运行，解释失败原因

步骤 2 之前不会写任何文件，步骤 4 和 5 各自都会停下来等你。

## 4. 前置条件

| 需要 | 什么时候 | 没有的话 |
|---|---|---|
| `git` + push 权限 | 全程 | 无法进行 |
| GitHub remote | 全程 | 不支持 —— action 只跑在 GitHub |
| repo admin 权限 | 步骤 5 | 得找有权限的人点一下那个开关 |
| `gh` 已登录 | 步骤 1、5、6 | 退化成给你链接自己点，功能不减 |
| token 的 `workflow` scope | 步骤 4，**仅 HTTPS remote** | push 会被拒；换 SSH，或跑 `gh auth refresh -h github.com -s workflow` |

---

以下是背景资料 —— 遇到问题时再看，不必预读。

## 附录 1 · 步骤 2 问的那两个问题

两个都是现在回答很便宜、事后搞错很贵的。

**当前版本号是多少？** 这个值用来播种 `.release-please-manifest.json`。播错了，下一次发版会从一个
很低的版本重新编号。而 tag 是会骗人的 —— 发布分支、打错的 tag、根本没发出去的 tag —— 所以侦察到的值
只是**报给你确认**，不会直接拿来用。

这件事**不等于**把版本控制权收回到你手上：

> manifest 只在初始化时由你写一次。第一次发版之后，这个文件归机器人所有，每次发版它自己重写。
> 播种起始版本相当于给里程表设个初始读数 —— 之后每一次跳版本仍然是 CI 在决定。

**要不要开 pre-1.0 护栏？** 只在版本低于 `1.0.0` 时才会问。`bump-minor-pre-major` 的官方定义是
「breaking changes only bump semver minor if version < 1.0.0」；`bump-patch-for-minor-pre-major` 是
「feature changes only bump semver patch if version < 1.0.0」。两者都**不改变提交语义如何被解读**，
只是在项目还年轻时把结果放缓。

如果你要求「只让 minor 往上加」，这个 skill 会**反过来劝你**，而不是照做。字面上能做到这件事的字段是
`versioning: always-bump-minor`，但它会让 commit 类型彻底失效 —— `fix:` 升 minor，`feat!:` 也升
minor —— 等于把 release-please 退化成一个 `+0.1.0` 计数器。官方给 `always-bump-*` 标注的用途是
**往维护分支回合补丁**，不是主分支日常发版。它会把你引向上面那组护栏，那才是真正对得上你意图的工具；
听完理由你仍然坚持，override 照写。

## 附录 2 · 为什么用 manifest 模式

manifest 模式是官方称的 "Manifest Driven release-please"，也是官方的主路径。
从 `release-please-action@v4` 起，官方「remove most configuration options in favor of manifest
configuration」，大量 action inputs 被删，配置的正确位置是配置文件而非 `with:`。
生成的 workflow 钉 `@v5`。

## 附录 3 · 深入

`skills/setup/references/gotchas.md` —— **每一条论断都标了置信度，撑不住的直接删掉而不是用低置信度糊过去。**
覆盖：HTTPS remote 的 `workflow` scope 那道墙、monorepo、用 `extra-files` 把版本号同步进源文件、
用 `release_created` 写只在发版那一刻才存在的值、分支保护冲突、用 PAT 触发下游 workflow。
