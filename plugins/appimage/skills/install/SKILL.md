---
name: install
description: Install a downloaded .AppImage into the system as a first-class desktop app — binary to /opt, icons into the hicolor theme, a validated .desktop entry, searchable in GNOME Activities with the correct icon and URL-scheme handling. Also upgrades an installed AppImage to a new version and fully uninstalls one. Use when the user asks to "install an AppImage", "integrate an AppImage into GNOME/the desktop", "make an AppImage show in the app menu / with its icon", "pin an AppImage", "upgrade/uninstall an AppImage", or 安装 AppImage / 把 AppImage 集成到桌面 / AppImage 图标显示成齿轮 / 升级或卸载 AppImage.
allowed-tools: Read, Glob, Grep, Bash(file *), Bash(chmod *), Bash(mktemp *), Bash(find *), Bash(ls *), Bash(cp *), Bash(mkdir *), Bash(gtk-update-icon-cache *), Bash(desktop-file-validate *), Bash(update-desktop-database *), Bash(dpkg *), Bash(sed *), Bash(xdg-mime *), Bash(xdg-open *), Bash(sudo -n *), Bash(for *), Bash(cat ~/.claude/plugins/installed_plugins.json)
---

# AppImage desktop integration

Turn a downloaded `*.AppImage` into a first-class desktop citizen: binary under a stable
path, searchable in GNOME Activities, correct icon instead of the gear placeholder,
pinnable to Dash, custom URL schemes (`myapp://`) wired up. Works on any
freedesktop-compliant DE (GNOME / KDE / XFCE / Cinnamon).

The whole job is giving the XDG specs three things: a **stable executable path**, a
**`.desktop` file**, and **hicolor icons**. Get all three right and the desktop picks the
app up by itself.

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
7. Never silently overwrite an existing install directory, desktop file, or installed
   icon — report what exists and ask.
8. **Never assume the install target.** Step 3 asks the user where things go. The three
   path variables defined there (`BIN_DIR`, `DESKTOP_DIR`, `ICON_ROOT`) are used by every
   later step — do not hardcode `/opt` or `~/.local/share` outside step 3.
9. sudo in a Claude Code session has **no TTY** — a bare `sudo` that needs a password
   fails with `a terminal is required to read the password`. Before the first sudo
   command, run the **Sudo authentication** procedure below.

## Sudo authentication (before the first sudo command)

1. Read `~/.claude/plugins/installed_plugins.json`. If the `core` plugin is installed →
   invoke `/core:sudo-auth` and continue with its result.
2. If core is **not** installed, show the charter's core-reminder (CHARTER.md §5) **once
   per session**, then continue with the built-in fallback below regardless of the answer
   (if the user installs core, use `/core:sudo-auth` from then on).
3. **Built-in fallback** — the same procedure `/core:sudo-auth` runs:

   ```bash
   sudo -n true 2>/dev/null && echo SUDO_OK || echo SUDO_NEEDS_AUTH
   for c in "$SUDO_ASKPASS" \
            /usr/libexec/gcr-ssh-askpass /usr/libexec/gcr4-ssh-askpass \
            /usr/libexec/ssh-askpass /usr/lib/ssh/ssh-askpass \
            /usr/bin/ssh-askpass /usr/bin/ksshaskpass; do
     [ -n "$c" ] && [ -x "$c" ] && { echo "ASKPASS=$c"; break; }
   done
   ```

   - `SUDO_OK` → proceed.
   - Helper found → hand the user `! SUDO_ASKPASS=<helper> sudo -A -v` (GUI password
     dialog; the password never enters the chat), then re-check `sudo -n true`.
   - No helper → offer: install `ssh-askpass-gnome` / `ksshaskpass` from their own
     terminal, or run this flow's sudo commands there. Do **not** suggest `sudo -v` in a
     separate terminal — sudo's `tty_tickets` means it won't unlock this session.
   - sudo credentials expire (~15 min default). A password error midway is expiry, not a
     bug — re-authenticate.

## Step 0 · Locate the AppImage, then preflight

**(a) Which AppImage?** Never assume one.

- The user passed a path (e.g. `/appimage:install ~/Downloads/Foo.AppImage`) → verify it
  exists and is a regular file. Doesn't exist → say so and stop; do not go hunting for a
  "similar" file on your own.
- No path given → search the likely spots and **ask the user to pick** (AskUserQuestion):

  ```bash
  find ~/Downloads ~/Desktop . -maxdepth 2 -name '*.AppImage' -type f 2>/dev/null
  ```

  Present the hits as options (with an "other / type a path" escape). If nothing turns up,
  just ask for the path outright. `~/Downloads` is a place to *look*, never a default.

**(b) Preflight** on the chosen file:

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

Ask **two** questions with AskUserQuestion before touching the system.

**(a) The slug** — lowercase short name used for the install dir and desktop filename,
derived from `Name`. Propose one, let the user correct it.

**(b) The install scope.** This decides all paths for the rest of the run. Offer:

| Scope | `BIN_DIR` (binary) | `DESKTOP_DIR` | `ICON_ROOT` | sudo needed | Visible to |
|---|---|---|---|---|---|
| **hybrid** (recommend first) | `/opt/<slug>` | `~/.local/share/applications` | `~/.local/share/icons/hicolor` | binary only | this user |
| **system** | `/opt/<slug>` | `/usr/share/applications` | `/usr/share/icons/hicolor` | everything | all users |
| **user** | `~/.local/opt/<slug>` | `~/.local/share/applications` | `~/.local/share/icons/hicolor` | none | this user |

Trade-offs to present with the options:

- **hybrid** — FHS-conventional binary location, root-owned so it can't be deleted by
  accident; integration is per-user. The default for a single-user machine.
- **system** — every user on the machine sees the app. Everything needs sudo, and the
  icon cache / desktop database commands must also run under sudo.
- **user** — no sudo at all; survives nothing breaks if the user has no sudo rights.
  Binary is user-writable (no accidental-deletion protection).

Then present the full plan in one block and confirm:

> Install `<Name>`?
> - slug: `<slug>` · scope: `<scope>`
> - binary → `<BIN_DIR>/<filename>` (755)
> - icons → `<ICON_ROOT>/<sizes>/apps/<icon>.png`
> - entry → `<DESKTOP_DIR>/<slug>.desktop`
> - Exec: `<BIN_DIR>/<filename> <args>`
> - URL schemes: `<schemes, if any>`

If the target install dir or desktop file already exists, say so here — see Hard rule 7.

**From here on, use the variables, not literal paths.** `SUDO` below means: prefix with
`sudo` when the scope requires it per the table, otherwise run bare.

## Step 4 · Install the binary

```bash
$SUDO mkdir -p <BIN_DIR>
$SUDO mv /abs/path/App.AppImage <BIN_DIR>/<filename>
$SUDO chmod 755 <BIN_DIR>/<filename>
# hybrid/system scopes only:
sudo chown root:root <BIN_DIR>/<filename>
```

Keep the versioned filename (`Foo_1.2.3.AppImage`): the desktop file pins the version,
which makes upgrades and rollback explicit. `mv`, not `cp` — one copy on disk.

## Step 5 · Icons

```bash
SRC="$tmp/squashfs-root/usr/share/icons/hicolor"
for sz in 16x16 24x24 32x32 48x48 64x64 128x128 192x192 256x256 512x512; do
  if [ -f "$SRC/$sz/apps/<icon>.png" ]; then
    $SUDO mkdir -p <ICON_ROOT>/$sz/apps
    $SUDO cp "$SRC/$sz/apps/<icon>.png" <ICON_ROOT>/$sz/apps/
  fi
done
$SUDO gtk-update-icon-cache -f -t <ICON_ROOT>
```

`<icon>` is the `Icon=` value from step 2. The `if` tolerates AppImages that ship only some
sizes. `-t` forces the rebuild — without it the first install into an empty directory is
sometimes skipped.

## Step 6 · Desktop file

Derive it from the extracted one — replace the `AppRun` token with the installed path, keep
everything else (including `%U` / `--no-sandbox` / `MimeType=` / `StartupWMClass=`):

```bash
sed -e "s|^Exec=AppRun|Exec=<BIN_DIR>/<filename>|" \
    "$tmp"/squashfs-root/*.desktop > <DESKTOP_DIR>/<slug>.desktop
$SUDO chmod 755 <DESKTOP_DIR>/<slug>.desktop   # sudo only if DESKTOP_DIR is root-owned
desktop-file-validate <DESKTOP_DIR>/<slug>.desktop   # must print nothing
$SUDO update-desktop-database <DESKTOP_DIR>
```

(For the system scope the file was written via a shell redirect — that needs
`sudo tee`, not `sudo sed ... >`. User scopes write directly.)

Read the result and sanity-check it. If the vendor's file is broken or missing fields, fix
it against the [Desktop Entry spec](https://specifications.freedesktop.org/desktop-entry-spec/latest/)
before validating again. If `sed` produced no substitution (vendor used something other
than `AppRun`), edit the `Exec=` line by hand.

## Step 7 · Verify

```bash
<BIN_DIR>/<filename> <args without %U>          # direct launch, outside the DE
grep -i '^Icon=' <DESKTOP_DIR>/<slug>.desktop
ls <ICON_ROOT>/*/apps/ | sort -u
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

New version downloaded, old one installed by this skill. Use the same paths as the
existing install (read the current desktop file to recover them — do not re-ask scope).

1. `chmod +x` the new file, `$SUDO mv` it into `<BIN_DIR>/` next to the old one
   (keep the old one as rollback until verified).
2. Point the desktop file at the new filename:
   `$SUDO sed -i 's|<old-filename>|<new-filename>|g; s|^X-AppImage-Version=.*|X-AppImage-Version=<new-ver>|' <DESKTOP_DIR>/<slug>.desktop`
3. `desktop-file-validate` again.
4. Reinstall icons **only if the new version changed them** (extract and compare).
5. Launch, verify, then ask before `$SUDO rm <BIN_DIR>/<old-filename>`.

## Uninstalling

Handled by the dedicated skill: **`/appimage:uninstall`** — it finds installed AppImages,
shows the full deletion list for confirmation, and removes binary + entry + icons.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| App not in Activities | invalid desktop file, or not 755 | `desktop-file-validate`; `chmod +x`; then re-login (Wayland) / SIGHUP (X11) |
| Grey gear icon | `Icon=` ≠ icon filename (case!), cache stale, or a symlink was copied | step 7's grep-vs-ls check; rerun `gtk-update-icon-cache -f -t`; recopy real PNGs |
| `libfuse.so.2` error | Ubuntu 24.04 lacks FUSE | `sudo apt install libfuse2t64` |
| Electron sandbox error | Chromium sandbox vs AppImage | keep `--no-sandbox` in `Exec=` |
| URL scheme dead | desktop database stale | `update-desktop-database`; then `xdg-mime default` explicitly |
| Files "missing" after extract | `--appimage-extract` reset the CWD | absolute paths everywhere (Hard rule 1) |
| `sudo: a terminal is required to read the password` | no TTY in this session | Sudo authentication section above |
| Other users can't see the app | hybrid/user scope installs are per-user | reinstall with the system scope |
