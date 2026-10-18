[English](README.md) | [中文](README.zh-CN.md)

# core

DeckHand's **shared primitives** — the capabilities every workflow plugin may call,
bundled into one install. This is the marketplace's standard library: small, universal,
no user-facing goal of its own. See [CHARTER.md](../../CHARTER.md) §1 for the two-layer
model.

Install it once and every DeckHand workflow that needs a primitive gets it silently;
without it, each workflow falls back to its own built-in (fully functional) procedure.

```
/plugin install core@deckhand
```

Core is a **bundle**: you install all of it, present and future primitives included —
there is nothing to pick.

## Skills

| Skill | Does |
|---|---|
| `/core:sudo-auth` | Makes sudo work inside a Claude Code session (no TTY): finds a GUI askpass helper, primes sudo's credential cache via one graphical password prompt |

## How workflows use core

A workflow that needs a primitive checks `~/.claude/plugins/installed_plugins.json` for
`core`, invokes the skill if present, and otherwise shows a one-time reminder with the
install command before continuing with its fallback. You are never auto-installed into
anything, and never blocked for declining.

## Adding a primitive

Primitives live here and nowhere else, and they must not call other plugins (charter §1:
dependencies point one way). One skill per primitive, verb-named.
