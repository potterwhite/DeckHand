# DeckHand

[English](README.md) | [中文](README.zh-CN.md)

**A deck hand does the repetitive, tedious, indispensable work.**

This repository is a Claude Code **plugin marketplace**. Each plugin is a
self-contained unit with its own README and skills — independent of the others,
installed on its own.

## Plugins

| Plugin | What it does | Docs |
|---|---|---|
| `release-please` | Configure a semantic auto-release pipeline for any GitHub repo | [README](plugins/release-please/README.md) |

## Install

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

Skills are namespaced by plugin name, so invoke with the prefix:

```
/release-please:setup
```

Browse what you have installed, and read load errors, with `/plugin`.

### Updating

Your machine holds a git clone of this repo, parked at one commit. New commits
here do not reach you automatically — pull them:

```
/plugin marketplace update deckhand
```

## Local development

A marketplace install loads a **cached snapshot** pinned to a pushed commit, not
your working tree — so editing `SKILL.md` appears to do nothing. Mount the
checkout instead:

```bash
claude --plugin-dir ./plugins/release-please    # local copy wins for the session
/reload-plugins                                  # after each edit
claude plugin validate ./plugins/release-please  # before committing
```

Plugin skills are namespaced and do **not** appear in `/skills` — invoke
`/release-please:setup`, and use `/plugin` to see what is loaded.

Full procedure and the failure modes that look like bugs: `/plugin-dev`.

## Adding a plugin

The hierarchy is settled. Adding something is just `mkdir` — no existing
structure needs to change:

```bash
mkdir -p plugins/NAME/{.claude-plugin,skills/SOME_SKILL}
```

Then write three files:

```
plugins/NAME/
├── .claude-plugin/plugin.json     # name / description / version
├── README.md                      # this unit's own docs
└── skills/SOME_SKILL/
    └── SKILL.md                   # frontmatter: name + description
```

Finally add an entry to the `plugins` array in the root
`.claude-plugin/marketplace.json` (`source` is a path relative to the repo root,
i.e. `./plugins/NAME`).

## Layout

```
DeckHand/
├── .claude-plugin/marketplace.json   ← the repo IS the marketplace; lists every plugin
└── plugins/
    └── release-please/               ← one self-contained unit
        ├── .claude-plugin/plugin.json
        ├── README.md
        └── skills/setup/
            ├── SKILL.md
            ├── templates/            ← static templates; the skill copies and substitutes
            └── references/           ← deep material, loaded on demand
```

**Note**: installing a plugin copies its directory into a cache, so plugins
**cannot** share files via `../` relative paths — every unit must be
self-contained.

## Design stance

No Python, no binaries, no runtime to install. Markdown instructions plus static
templates, nothing else.

Because the hard part of this kind of work was never computation, it was
judgement: is this a monorepo? Is the tag prefix `v` or bare? Should an existing
CHANGELOG be preserved or taken over? What is that failure log actually saying?
There are too many special cases; encoding them as if-elif only guarantees
breakage on the repos that are actually interesting. Judgement goes to the model,
the deterministic parts go to static templates.

## License

MIT
