---
name: uninstall
description: Remove an AppImage that was installed as a desktop app — finds which AppImages are installed (desktop entries pointing into /opt or ~/.local/opt), asks which one to remove, shows the complete deletion list for confirmation, then removes the binary directory, the .desktop entry, every icon size, and refreshes the caches. Use when the user asks to "uninstall an AppImage", "remove an AppImage from the system/GNOME", "delete an installed AppImage", or 卸载 AppImage / 删除安装的 AppImage.
allowed-tools: Read, Glob, Grep, Bash(grep *), Bash(ls *), Bash(file *), Bash(sudo -n *), Bash(for *), Bash(gtk-update-icon-cache *), Bash(update-desktop-database *), Bash(cat ~/.claude/plugins/installed_plugins.json)
---

# AppImage uninstall

Remove an AppImage that was integrated into the desktop (by `/appimage:install` or by
hand): the binary directory, the `.desktop` entry, all hicolor icon sizes, and the caches.
The desktop file is the source of truth — paths are recovered from it, never assumed.

## Market principles

<!-- charter:begin -->
These rules come from DeckHand's CHARTER.md and bind every plugin. Do not edit them
here — edit the charter and re-sync.

1. **Ask, don't assume.** If the user didn't specify a target (file, app, path, scope),
   search the likely spots and ask — never pick silently.
2. **Stop before the irreversible.** Show exactly what will change, and get explicit
   confirmation, before any destructive or system-wide action.
3. **Never ask for secrets in chat.** Authentication happens through the OS (a GUI
   askpass dialog, the user's own terminal) — never by pasting passwords into the
   conversation.
4. **Compose with core, degrade gracefully.** When a core capability exists, invoke it
   (`/core:<skill>`). If core is not installed, offer it once per session, then continue
   with this skill's built-in fallback — the fallback must be fully functional.
<!-- charter:end -->

## Hard rules

1. **Never guess which app to remove.** List the candidates found on disk and let the
   user pick. If the user named an app and it's not among the candidates, say so and show
   what *is* installed — do not "closest-match" your way to deleting the wrong thing.
2. Recover every path from the desktop file's own fields. Do not assume an install scope.
3. The complete deletion list is shown and confirmed (AskUserQuestion) **before** any
   `rm` runs — above all before `sudo rm -rf`.
4. sudo here has no TTY. If sudo credentials are needed and not cached, authenticate the
   same way `/appimage:install` does: `/core:sudo-auth` when the core plugin is installed
   (check `~/.claude/plugins/installed_plugins.json`), otherwise its built-in fallback.
5. If the app is running, ask the user to close it first — removing the binary from under
   a running process is asking for a confusing session.

## Step 1 · Find installed AppImages

Desktop entries whose `Exec=` points into an AppImage install dir are the inventory:

```bash
grep -l '^Exec=/opt/' ~/.local/share/applications/*.desktop \
                      /usr/share/applications/*.desktop 2>/dev/null
grep -l "^Exec=$HOME/.local/opt/" ~/.local/share/applications/*.desktop 2>/dev/null
```

For each hit, read the file and record: `Name`, the `Exec=` path (→ the binary dir),
`Icon=` (→ the icon logical name), and which directory the desktop file lives in
(→ the install scope: `/usr/share/...` = system, `~/.local/share/...` = hybrid or user).

No hits at all → say so plainly and stop. Nothing to uninstall.

## Step 2 · Pick and confirm (stop and ask)

If the user already named an app, match it against the candidates; no match → report and
show the list. Otherwise present the candidates and ask which to remove.

Then show the **complete deletion list** and get explicit confirmation:

> Remove `<Name>`? This will delete:
> - `<BIN_DIR>/` (the AppImage binary, `<size>`)
> - `<DESKTOP_DIR>/<slug>.desktop`
> - `<ICON_ROOT>/*/apps/<icon>.png` (`<n>` sizes)
> - and rebuild the icon cache + desktop database

## Step 3 · Authenticate sudo if needed

`sudo -n true` — if the binary dir or desktop file is root-owned and credentials aren't
cached, run the sudo-authentication procedure (Hard rule 4) before continuing.

## Step 4 · Remove

```bash
$SUDO rm -rf <BIN_DIR>
$SUDO rm <DESKTOP_DIR>/<slug>.desktop
$SUDO rm <ICON_ROOT>/*/apps/<icon>.png
$SUDO gtk-update-icon-cache -f -t <ICON_ROOT>
$SUDO update-desktop-database <DESKTOP_DIR>
```

`$SUDO` = `sudo` for root-owned paths, bare for user-owned ones.

## Step 5 · Verify

```bash
ls <BIN_DIR> 2>&1                          # should be "No such file or directory"
ls <DESKTOP_DIR>/<slug>.desktop 2>&1       # same
ls <ICON_ROOT>/*/apps/<icon>.png 2>&1      # same
```

Report done. On **Wayland**, mention the entry may linger in GNOME Activities until the
user logs out and back in; on X11 `killall -SIGHUP gnome-shell` refreshes immediately.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| App not in the candidate list | it was never desktop-integrated (just a bare binary in ~/Downloads etc.) | say so; offer to just delete the file |
| Entry still searchable after removal | GNOME index stale | re-login (Wayland) / SIGHUP gnome-shell (X11) |
| `Permission denied` on rm | root-owned paths, no cached sudo | step 3 |
| Leftover config/cache dirs (`~/.config/<app>`) | app data, not part of the install | mention them, ask before deleting — user data may matter |
