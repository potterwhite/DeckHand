[English](README.md) | [中文](README.zh-CN.md)

# appimage

Install a downloaded `*.AppImage` as a first-class desktop citizen on Ubuntu / GNOME (and
any freedesktop-compliant DE): the binary goes to `/opt` root-owned, icons go into the
hicolor theme, a validated `.desktop` entry makes it searchable in Activities with the real
icon, pinnable to Dash, and wired up for custom URL schemes (`myapp://`). Also upgrades an
installed AppImage to a new version and fully uninstalls one.

## 1. Skill

| Skill | Does |
|---|---|
| `/appimage:install` | Full lifecycle: install → verify → upgrade → uninstall |

## 2. Use

Not installed yet? See the [repo README](../../README.md#2-install).

Run it anywhere, with the AppImage already downloaded:

```
/appimage:install ~/Downloads/Foo_1.2.3.AppImage
```

## 3. What it does

1. **Preflight** — checks the file is really an AppImage (`ELF 64-bit`), `chmod +x`, and
   that FUSE (`libfuse2t64` on Ubuntu 24.04) is present
2. **Extract** — pulls the vendor's own `.desktop` file and icons out of the AppImage with
   `--appimage-extract`, instead of writing anything from scratch
3. **Confirm** — asks you the slug and the **install scope** (hybrid `/opt` + per-user
   integration, fully system-wide, or fully user-local with no sudo), shows the full plan
   (every target path, the `Exec=` line, URL schemes), and stops for approval before
   touching the system
4. **Install** — binary to `/opt/<slug>/` (sudo, root:root 755), all shipped icon sizes to
   `~/.local/share/icons/hicolor/`, desktop file to `~/.local/share/applications/` with only
   the `AppRun` token replaced by the real path
5. **Verify** — validates the desktop file (GNOME silently rejects invalid ones), launches
   the binary directly, cross-checks the `Icon=` name against the installed icon files,
   binds and tests URL schemes
6. **Cleanup** — removes the extraction temp dir; the AppImage was moved, not copied

Steps 4's sudo commands prompt for your password in the terminal — expected, not a failure.

## 4. Prerequisites

| Needed | When | Without it |
|---|---|---|
| sudo access | binary install to `/opt` | cannot proceed (icons and desktop file are user-level, but the binary isn't) |
| `libfuse2t64` | running the AppImage on Ubuntu 24.04 | the app won't start; the skill tells you the apt command |
| `desktop-file-utils`, `gtk-update-icon-cache`, `xdg-utils` | validation, icon cache, scheme binding | standard on Ubuntu desktop; verification degrades gracefully |
| Wayland: a re-login | after install, occasionally | the entry may not appear until you log out/in — the skill says so when relevant |
