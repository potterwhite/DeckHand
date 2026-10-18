# DeckHand

[English](README.md) | [中文](README.zh-CN.md)

**A deck hand does the repetitive, tedious, indispensable work.**

This repository is a Claude Code **plugin marketplace**. Each plugin is a
self-contained unit with its own README and skills — independent of the others,
installed on its own.

**Which section you want:**

| What you're doing | Read |
|---|---|
| Installing and getting started | 1 → 2 → 3 |
| Upgrading to the latest version | 4 |
| Editing a skill in this repo | Appendix 1 |
| Adding a new plugin | Appendix 2 |

---

## 1. Plugins

| Plugin | What it does | Docs |
|---|---|---|
| `release-please` | Configure a semantic auto-release pipeline for any GitHub repo | [README](plugins/release-please/README.md) |
| `appimage` | Install a .AppImage as a first-class desktop citizen (`/opt`, icons, `.desktop`, URL schemes) | [README](plugins/appimage/README.md) |

## 2. Install

Two commands, and you need both. `marketplace add` only fetches the catalog —
it installs nothing by itself:

```
/plugin marketplace add potterwhite/DeckHand
/plugin install release-please@deckhand
```

Copy them exactly. The two identifiers are different strings and are not
interchangeable:

| Argument | Comes from | Case |
|---|---|---|
| `potterwhite/DeckHand` | the GitHub repo path | as written — `DeckHand`, two capitals |
| `release-please@deckhand` | `name` in `.claude-plugin/marketplace.json` | all lowercase |

Getting the case wrong on either one makes the command fail.

If the install summary prints `Run /reload-plugins to activate.`, run it.

## 3. Use

Skills are namespaced by plugin name, so invoke with the prefix:

```
/release-please:setup
```

Plugin skills do **not** appear in `/skills` — that is by design, not a broken
install. Browse what you have, and read load errors, with `/plugin`.

## 4. Updating

Your machine holds a git clone of this repo, parked at one commit. New commits
here do not reach you automatically — pull them:

```
/plugin marketplace update deckhand
```

---

Everything below is only for people changing this repo.

## Appendix 1 · Local development

A marketplace install loads a **cached snapshot** pinned to a pushed commit, not
your working tree — so editing `SKILL.md` appears to do nothing. Mount the
checkout instead:

```bash
claude --plugin-dir ./plugins/release-please    # local copy wins for the session
/reload-plugins                                  # after each edit
claude plugin validate ./plugins/release-please  # before committing
```

Full procedure and the failure modes that look like bugs: `/plugin-dev`.

## Appendix 2 · Adding or changing a plugin

Everything about contributing — the two-layer model (workflows vs `core`), naming,
admission rules, the plugin skeleton, the runtime-discipline master block that every
SKILL.md embeds, and the design stance — lives in **[CHARTER.md](CHARTER.md)**, the
single source of truth. This README deliberately does not repeat it.

Two mechanical notes worth knowing even as a user:

- Installing a plugin copies its directory into a cache, so plugins cannot share files
  via `../` relative paths — every unit is self-contained.
- Pushing to `main` does not reach users by itself; a change ships when the plugin's
  `version` is bumped (see CHARTER.md § Versioning).

## License

MIT
