[English](README.md) | [中文](README.zh-CN.md)

# appimage

把下载来的 `*.AppImage` 装成 Ubuntu / GNOME（以及任何遵循 freedesktop 规范的桌面）里的
一等公民：二进制放进 `/opt`（root 所有），图标铺进 hicolor 主题，生成通过校验的
`.desktop` 入口 —— Activities 里能搜到、显示真图标、能 pin 到 Dash，自定义 URL scheme
（`myapp://`）也能调起。同一条 skill 还负责升级到新版本。

## 1. Skills

| Skill | 作用 |
|---|---|
| `/appimage:install` | 安装 → 验证 → 升级 |
| `/appimage:uninstall` | 找到已装的 AppImage，确认完整删除清单，移除二进制 + 入口 + 图标 |

## 2. 使用

还没装？看[仓库 README](../../README.zh-CN.md#2-安装)。

AppImage 下载好后，在任意目录运行。可以带上路径；不带参数它会搜常见位置并问你要装
哪一个：

```
/appimage:install ~/Downloads/Foo_1.2.3.AppImage
/appimage:install
```

## 3. 它做什么

1. **定位 + 预检** —— 没带路径时会搜常见位置并问你要装哪一个（绝不默认
   `~/Downloads`）；然后确认文件真是 AppImage（`ELF 64-bit`）、`chmod +x`、检查 FUSE
   （Ubuntu 24.04 上是 `libfuse2t64`）是否在位
2. **提取** —— 用 `--appimage-extract` 把 AppImage 自带的 `.desktop` 文件和图标解出来，
   直接抄官方的，不手写
3. **确认** —— 先问你 slug 和**安装范围**（hybrid：`/opt` + 当前用户集成；system：全系统
   所有用户可见；user：纯用户目录、零 sudo），列出完整计划（每个目标路径、`Exec=` 行、
   URL scheme），停下来等你批准后才动系统
4. **安装** —— 二进制进 `/opt/<slug>/`（sudo，root:root 755），所有尺寸的图标进
   `~/.local/share/icons/hicolor/`，desktop 文件进 `~/.local/share/applications/`，
   只把 `AppRun` 换成真实路径，其余参数原样保留
5. **验证** —— 校验 desktop 文件（GNOME 对非法文件是静默拒收的）、直接启动二进制、
   交叉核对 `Icon=` 和实际图标文件名、绑定并测试 URL scheme
6. **清理** —— 删除解压临时目录；AppImage 是 `mv` 不是 `cp`，Downloads 里不留副本

第 4 步的 sudo 命令会在终端里提示输密码 —— 正常现象，不是失败。

## 4. 前提

| 需要 | 什么时候 | 没有会怎样 |
|---|---|---|
| sudo 权限 | 装二进制到 `/opt`（hybrid/system 范围） | 选 `user` 范围 —— 零 sudo |
| DeckHand `core` plugin | sudo 认证 | 可选的便利：一次图形密码弹窗管整个会话；不装则 skill 用内置的同一套流程 |
| `libfuse2t64` | 在 Ubuntu 24.04 上运行 AppImage | 应用起不来；skill 会告诉你 apt 命令 |
| `desktop-file-utils`、`gtk-update-icon-cache`、`xdg-utils` | 校验、图标缓存、scheme 绑定 | Ubuntu 桌面版默认都有；缺了验证会降级但不会出错 |
| Wayland：重新登录 | 装完后偶尔需要 | 条目不重新登录可能不出现 —— 需要时 skill 会明说 |
