---
name: sudo-auth
description: Make sudo work inside a Claude Code session, where there is no TTY and any password prompt fails with "a terminal is required to read the password". Checks cached credentials, finds a graphical askpass helper (gcr / ssh-askpass / ksshaskpass), hands the user the exact command to authenticate via a GUI dialog, and verifies. Use before any flow that needs sudo, when a sudo command fails with "a terminal is required" or "a password is required", or sudo 要密码但没有终端 / sudo 无法弹出密码提示.
allowed-tools: Bash(sudo -n *), Bash(cat ~/.claude/plugins/installed_plugins.json), Bash(for *), Bash(ls *), Bash(echo *)
---

# sudo auth inside a Claude Code session

Claude Code's Bash tool — and the `!` prefix — run **without a TTY**. Any `sudo` that
needs a password dies with `sudo: a terminal is required to read the password`. This
skill gets credentials cached so that subsequent sudo calls in the session succeed
silently. Invoke it *before* a multi-step privileged flow, not after the first failure.

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

1. **Never** ask the user to paste their password into the chat, and never use
   `echo password | sudo -S`. Authentication happens in the GUI dialog or the user's
   own terminal, nowhere else.
2. Detect the askpass helper at runtime — never hardcode a path. Distros and desktops
   differ.
3. This skill changes nothing on the system. It only primes sudo's credential cache.

## Step 1 · Check whether sudo already works

```bash
sudo -n true 2>/dev/null && echo SUDO_OK || echo SUDO_NEEDS_AUTH
```

`SUDO_OK` → done. Report and stop; the caller can proceed.

## Step 2 · Find a graphical askpass helper

```bash
for c in "$SUDO_ASKPASS" \
         /usr/libexec/gcr-ssh-askpass /usr/libexec/gcr4-ssh-askpass \
         /usr/libexec/ssh-askpass /usr/lib/ssh/ssh-askpass \
         /usr/bin/ssh-askpass /usr/bin/ksshaskpass; do
  [ -n "$c" ] && [ -x "$c" ] && { echo "ASKPASS=$c"; break; }
done
```

Honor a set `$SUDO_ASKPASS` first, then probe the usual GNOME/KDE locations.

## Step 3 · Hand the user the exact command

**Helper found** → tell the user (in their language):

> Sudo needs your password, but this session has no terminal for the prompt. Run this —
> it pops up a normal graphical password dialog:
>
> ```
> ! SUDO_ASKPASS=<helper> sudo -A -v
> ```
>
> The `!` prefix runs it inside this session. Your password goes to the dialog, never
> into the chat.

**No helper found** → offer the two real options and let the user pick:

1. In their own terminal: `sudo apt install ssh-askpass-gnome` (GNOME) or
   `sudo apt install ksshaskpass` (KDE), then come back — step 2 will find it.
2. Or: run the privileged commands this flow prints in their own terminal instead.

Do not suggest `sudo -v` in a separate terminal as a fix: with sudo's default
`tty_tickets`, credentials cached on another TTY do not unlock this session.

## Step 4 · Verify

```bash
sudo -n true 2>/dev/null && echo SUDO_OK || echo SUDO_STILL_FAILING
```

- `SUDO_OK` → report success; the caller proceeds.
- Still failing → the usual causes: wrong password (retry from step 3), the dialog was
  dismissed, or the timestamp expired. Re-authenticate from step 3.

## Expiry note

sudo's default `timestamp_timeout` is 15 minutes. If a long flow hits a password error
midway, that is not a bug — re-run this skill (step 1 will confirm) and continue.
