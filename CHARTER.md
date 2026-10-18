# DeckHand Charter

The single source of truth for how plugins in this marketplace are built.

- **README.md** tells *users* how to install and run plugins.
- **This file** tells *authors* (human or model) how to add and change plugins.

If any other file disagrees with this one, this one wins — fix the other file.
This charter is English-only on purpose: the master block in §4 is copied verbatim into
skill files, and a second language would create a second master.

## 1. Two layers

The layers are visible in the directory layout itself:

| Layer | Directory | What | Examples | Installed |
|---|---|---|---|---|
| **Primitives** | `primitives/` | Shared capabilities workflows call — the standard library | `core:sudo-auth` | as a whole, never in parts |
| **Workflows** | `plugins/` | Plugins that deliver a complete user goal | `release-please`, `appimage` | à la carte |

`primitives/` currently holds exactly one plugin, `core`, which bundles every primitive
(§6). If a future primitive ever outgrows the bundle, `primitives/` is where its plugin
would go — never `plugins/`.

Dependencies point one way only: **workflows may call `core`; `core` calls nothing.**

## 2. Rules live here only

Governance rules appear in this file and nowhere else. README and CLAUDE.md link here
instead of repeating. One deliberate exception: the runtime-discipline block (§4) is
*copied* into every SKILL.md, because only text inside the skill file reaches the running
model. The charter is the master; the copies are enforced by CI (planned) and by review.

## 3. Naming

- **Plugin = noun**: `appimage`, `release-please`, `core`.
- **Skill = verb**: `install`, `uninstall`, `sudo-auth`.
- Invocation is therefore always `/noun:verb`.

## 4. Runtime discipline (master block)

Every SKILL.md embeds the block below **verbatim**, right after the title/intro and before
its own Hard rules. Never edit the block inside a plugin — edit it here and re-sync every
plugin in the same commit. The `charter:begin/end` markers exist so CI can diff each copy
against this master byte-for-byte.

```markdown
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
```

## 5. Composition and the core-reminder UX

When a workflow needs a core capability:

1. Check whether core is installed: read `~/.claude/plugins/installed_plugins.json`.
2. **Installed** → invoke `/core:<skill>` without ceremony.
3. **Not installed** → show the reminder **once per session**, then continue with the
   built-in fallback.

Reminder rules (anti-dark-pattern):

- Never auto-install anything. The install command is typed by the user, always.
- Once per session per workflow. A "no" is remembered for the rest of the session.
- State the benefit, the cost (one more entry in the plugin list), and the exact command.
  Neutral wording, no urgency, no guilt.
- The "don't install" path is first-class: same outcome, slightly more manual.

Suggested reminder text (translate to the user's language):

```
This step needs sudo.

DeckHand's core toolkit turns this into a single GUI password prompt, and every
sudo for the next ~15 minutes goes through silently — for this workflow and any
future one.

  Install (one command; core is a bundle, present and future primitives included):
    /plugin install core@deckhand

  1. Install core, then continue (recommended)
  2. Skip — use this skill's built-in procedure (same result, one manual step)
```

## 6. Admission

A plugin belongs in DeckHand only if **all** of these hold:

- The chore is repetitive, tedious, and **judgment-heavy** — a deterministic script would
  do it worse, not better.
- It is **markdown + static templates only**: no runtime, no binaries, nothing to install.
- Its purpose is nameable in **one sentence**.
- It fits the two-layer model (§1) — a workflow, or a primitive that belongs in `core`.

## Plugin skeleton

```
DeckHand/
├── .claude-plugin/marketplace.json   # the repo IS the marketplace; lists every plugin
├── CHARTER.md                        # this file
├── primitives/                       # the standard library layer
│   └── core/
└── plugins/                          # the workflow layer
    └── <noun>/
        ├── .claude-plugin/plugin.json   # fixed field set: name, description, version,
        │                                #   author, homepage, repository, license
        ├── README.md                    # English
        ├── README.zh-CN.md              # 中文
        └── skills/<verb>/
            └── SKILL.md
            # templates/ and references/ only when the skill genuinely needs them
```

`primitives/core/` uses the identical internal skeleton — the layers differ in purpose
and install semantics, not in file layout.

Every SKILL.md uses the same internal order:

1. frontmatter (`name`, `description`, `allowed-tools`)
2. title + one-paragraph purpose
3. the Market principles block (§4, verbatim)
4. Hard rules (plugin-local; may tighten, never contradict, the Market principles)
5. numbered steps
6. (optional) troubleshooting table

## Versioning

Changing a SKILL.md requires bumping `version` in that plugin's `plugin.json` **in the
same commit** — users update against pushed versions, and an un-bumped change never
reaches them.
