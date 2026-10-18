---
name: install
description: Install a downloaded .AppImage into the system as a first-class desktop app — binary to /opt, icons into the hicolor theme, a validated .desktop entry, searchable in GNOME Activities with the correct icon and URL-scheme handling. Also upgrades an installed AppImage to a new version and fully uninstalls one. Use when the user asks to "install an AppImage", "integrate an AppImage into GNOME/the desktop", "make an AppImage show in the app menu / with its icon", "pin an AppImage", "upgrade/uninstall an AppImage", or 安装 AppImage / 把 AppImage 集成到桌面 / AppImage 图标显示成齿轮 / 升级或卸载 AppImage.
allowed-tools: Read, Glob, Grep, Bash(file *), Bash(chmod *), Bash(mktemp *), Bash(find *), Bash(ls *), Bash(cp *), Bash(mkdir *), Bash(gtk-update-icon-cache *), Bash(desktop-file-validate *), Bash(update-desktop-database *), Bash(dpkg *), Bash(sed *), Bash(xdg-mime *), Bash(xdg-open *)
---

# AppImage desktop integration

Turn a downloaded `*.AppImage` into a first-class desktop citizen: binary under `/opt`
(root-owned, shared system-wide), searchable in GNOME Activities, correct icon instead of
the gear placeholder, pinnable to Dash, custom URL schemes (`myapp://`) wired up. Works on
any freedesktop-compliant DE (GNOME / KDE / XFCE / Cinnamon).

The whole job is giving the XDG specs three things: a **stable executable path**, a
**`.desktop` file**, and **hicolor icons**. Get all three right and the desktop picks the
app up by itself.

## Hard rules

1. Extract only into a fresh `mktemp -d`, and use **absolute paths for everything
   afterwards** — `--appimage-extract` resets the shell's CWD to `$HOME` when it finishes.
2. Quote the extract globs in single quotes (`'*.desktop'`) or the shell expands them first.
3. Icons come only from `usr/share/icons/hicolor/<size>/apps/` inside the extraction. The
   `<name>.png` at the squashfs root is a (broken) symlink — never copy it.
4. `Icon=` in the desktop file is a **logical name**: no path, no extension, case-sensitive,
   and it must exactly equal the icon filename. `Icon=Foo` + `foo.png` = gear icon.
5. Never drop `%U` / `%F` or vendor args like `--no-sandbox` from `Exec=` — replace only the
   `AppRun` token with the absolute path of the installed AppImage.
6. `desktop-file-validate` must exit clean before you declare done. GNOME silently ignores
   invalid desktop files — this is the #1 "I installed it but can't find it" cause.
7. Never silently overwrite an existing `/opt/<slug>/`, desktop file, or installed icon —
   report what exists and ask.
8. sudo commands prompt for the password in the terminal — that is expected, not a failure.
   If sudo fails with an auth error, ask the user to run `! sudo -v` first, then retry.

## Step 0 · Preflight

```bash
file <APPIMAGE>                     # must say "ELF 64-bit LSB executable"
chmod +x <APPIMAGE>
dpkg -l libfuse2t64 2>/dev/null | grep ^ii
```

- `file` says `HTML document` or `Zip archive` → broken download or not an AppImage. Stop.
- FUSE missing on Ubuntu 24.04 → most AppImages won't run; tell the user
  `sudo apt install libfuse2t64` and continue once installed.

## Step 1 · Extract the bundled desktop file and icons

Every AppImage ships its own `.desktop` file and icons (the format requires it). Copying
them beats writing from scratch.

```bash
tmp=$(mktemp -d)
(cd "$tmp" && /abs/path/App.AppImage --appimage-extract '*.desktop' >/dev/null && \
              /abs/path/App.AppImage --appimage-extract 'usr/share/icons/*' >/dev/null)
```

## Step 2 · Inspect

```bash
cat "$tmp"/squashfs-root/*.desktop
find "$tmp/squashfs-root/usr/share/icons" -name '*.png'
```

Record from the desktop file: `Name`, `Icon` (the logical name), `StartupWMClass`,
`MimeType` (URL schemes), `Categories`, `Comment`, and the **argument tail** of `Exec=`
(everything after `AppRun`, e.g. `--no-sandbox %U`). Note which icon sizes exist.

## Step 3 · Confirm the plan (stop and ask)

Present the full plan and confirm with AskUserQuestion before touching the system:

> Install `<Name>`?
> - slug: `<slug>` (lowercase, from the app name)
> - binary → `/opt/<slug>/<filename>` (root:root, 755)
> - icons → `~/.local/share/icons/hicolor/<sizes>/apps/<icon>.png`
> - entry → `~/.local/share/applications/<slug>.desktop`
> - Exec: `/opt/<slug>/<filename> <args>`
> - URL schemes: `<schemes, if any>`

If `/opt/<slug>/` or the desktop file already exists, say so here — see Hard rule 7.

## Step 4 · Install the binary (sudo)

```bash
sudo mkdir -p /opt/<slug>
sudo mv /abs/path/App.AppImage /opt/<slug>/<filename>
sudo chmod 755 /opt/<slug>/<filename>
sudo chown root:root /opt/<slug>/<filename>
```

Keep the versioned filename (`Foo_1.2.3.AppImage`): the desktop file pins the version,
which makes upgrades and rollback explicit. `mv`, not `cp` — one copy on disk.

## Step 5 · Icons (user-level)

```bash
SRC="$tmp/squashfs-root/usr/share/icons/hicolor"
for sz in 16x16 24x24 32x32 48x48 64x64 128x128 192x192 256x256 512x512; do
  if [ -f "$SRC/$sz/apps/<icon>.png" ]; then
    mkdir -p ~/.local/share/icons/hicolor/$sz/apps
    cp "$SRC/$sz/apps/<icon>.png" ~/.local/share/icons/hicolor/$sz/apps/
  fi
done
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor
```

`<icon>` is the `Icon=` value from step 2. The `if` tolerates AppImages that ship only some
sizes. `-t` forces the rebuild — without it the first install into an empty directory is
sometimes skipped.

## Step 6 · Desktop file (user-level)

Derive it from the extracted one — replace the `AppRun` token with the installed path, keep
everything else (including `%U` / `--no-sandbox` / `MimeType=` / `StartupWMClass=`):

```bash
sed -e "s|^Exec=AppRun|Exec=/opt/<slug>/<filename>|" \
    "$tmp"/squashfs-root/*.desktop > ~/.local/share/applications/<slug>.desktop
chmod +x ~/.local/share/applications/<slug>.desktop
desktop-file-validate ~/.local/share/applications/<slug>.desktop   # must print nothing
update-desktop-database ~/.local/share/applications
```

Read the result and sanity-check it. If the vendor's file is broken or missing fields, fix
it against the [Desktop Entry spec](https://specifications.freedesktop.org/desktop-entry-spec/latest/)
before validating again. If `sed` produced no substitution (vendor used something other
than `AppRun`), edit the `Exec=` line by hand.

## Step 7 · Verify

```bash
/opt/<slug>/<filename> <args without %U>     # direct launch, outside the DE
grep -i '^Icon=' ~/.local/share/applications/<slug>.desktop
ls ~/.local/share/icons/hicolor/*/apps/ | sort -u
```

- Direct launch must work; if it fails, everything downstream is moot. Common failures:
  `Permission denied` (chmod), `libfuse.so.2` (step 0), Electron sandbox errors (add
  `--no-sandbox` to `Exec=` in the desktop file).
- The `Icon=` value must appear verbatim in the icon listing.
- URL scheme declared? Bind and test: `xdg-mime default <slug>.desktop x-scheme-handler/<scheme>`,
  then `xdg-open '<scheme>://test'`.
- GNOME Activities search indexes the directory by itself. If the entry doesn't appear:
  re-check validation and permissions (755), then on **X11** `killall -SIGHUP gnome-shell`;
  on **Wayland** the user must log out and back in — tell them, don't try to restart the
  Shell (it is the compositor; killing it kills the session).

## Step 8 · Cleanup

```bash
rm -rf "$tmp"
```

The AppImage was moved, not copied, so `~/Downloads` is already clean.

## Upgrade flow

New version downloaded, old one installed by this skill:

1. `chmod +x` the new file, `sudo mv` it into `/opt/<slug>/` next to the old one
   (keep the old one as rollback until verified).
2. Point the desktop file at the new filename:
   `sed -i 's|<old-filename>|<new-filename>|g; s|^X-AppImage-Version=.*|X-AppImage-Version=<new-ver>|' ~/.local/share/applications/<slug>.desktop`
3. `desktop-file-validate` again.
4. Reinstall icons **only if the new version changed them** (extract and compare).
5. Launch, verify, then ask before `sudo rm /opt/<slug>/<old-filename>`.

## Uninstall flow

```bash
sudo rm -rf /opt/<slug>
rm ~/.local/share/applications/<slug>.desktop
rm ~/.local/share/icons/hicolor/*/apps/<icon>.png
gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor
update-desktop-database ~/.local/share/applications
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| App not in Activities | invalid desktop file, or not 755 | `desktop-file-validate`; `chmod +x`; then re-login (Wayland) / SIGHUP (X11) |
| Grey gear icon | `Icon=` ≠ icon filename (case!), cache stale, or a symlink was copied | step 7's grep-vs-ls check; rerun `gtk-update-icon-cache -f -t`; recopy real PNGs |
| `libfuse.so.2` error | Ubuntu 24.04 lacks FUSE | `sudo apt install libfuse2t64` |
| Electron sandbox error | Chromium sandbox vs AppImage | keep `--no-sandbox` in `Exec=` |
| URL scheme dead | desktop database stale | `update-desktop-database`; then `xdg-mime default` explicitly |
| Files "missing" after extract | `--appimage-extract` reset the CWD | absolute paths everywhere (Hard rule 1) |
