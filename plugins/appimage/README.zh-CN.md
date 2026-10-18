[English](README.md) | [中文](README.zh-CN.md)

# appimage

把下载来的 `*.AppImage` 装成 Ubuntu / GNOME（以及任何遵循 freedesktop 规范的桌面）里的
一等公民：二进制放进 `/opt`（root 所有），图标铺进 hicolor 主题，生成通过校验的
`.desktop` 入口 —— Activities 里能搜到、显示真图标、能 pin 到 Dash，自定义 URL scheme
（`myapp://`）也能调起。同一条 skill 还负责升级到新版本和彻底卸载。

## 1. Skill

| Skill | 作用 |
|---|---|
| `/appimage:install` | 全生命周期：安装 → 验证 → 升级 → 卸载 |

## 2. 使用

还没装？看[仓库 README](../../README.zh-CN.md#2-安装)。

AppImage 下载好后，在任意目录运行：

```
/appimage:install ~/Downloads/Foo_1.2.3.AppImage
```

## 3. 它做什么

1. **预检** —— 确认文件真是 AppImage（`ELF 64-bit`）、`chmod +x`、检查 FUSE
   （Ubuntu 24.04 上是 `libfuse2t64`）是否在位
2. **提取** —— 用 `--appimage-extract` 把 AppImage 自带的 `.desktop` 文件和图标解出来，
   直接抄官方的，不手写
3. **确认** —— 列出完整计划（slug、每个目标路径、`Exec=` 行、URL scheme），停下来等你
   批准后才动系统
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
| sudo 权限 | 装二进制到 `/opt` | 无法进行（图标和 desktop 文件是用户级的，但二进制不是） |
| `libfuse2t64` | 在 Ubuntu 24.04 上运行 AppImage | 应用起不来；skill 会告诉你 apt 命令 |
| `desktop-file-utils`、`gtk-update-icon-cache`、`xdg-utils` | 校验、图标缓存、scheme 绑定 | Ubuntu 桌面版默认都有；缺了验证会降级但不会出错 |
| Wayland：重新登录 | 装完后偶尔需要 | 条目不重新登录可能不出现 —— 需要时 skill 会明说 |
