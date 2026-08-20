---
name: plugin-dev
description: Load this repo's plugin skills from the working tree instead of the installed marketplace snapshot. Use when a plugin skill here looks missing, stale or broken, when edits to SKILL.md have no effect, or when starting local plugin development.
allowed-tools: Read, Glob, Bash(cat ~/.claude/plugins/installed_plugins.json), Bash(git rev-parse *), Bash(git log *), Bash(claude plugin validate *)
---

# Load this repo's plugin skills locally

## 1. Check which copy is loaded

```bash
cat ~/.claude/plugins/installed_plugins.json
```

`gitCommitSha` ≠ the commit you are working on → a cached snapshot is loaded, not your working tree.

## 2. Mount the working tree

```bash
claude --plugin-dir ./plugins/<name>
```

On a name clash the local copy wins for that session. No need to uninstall.

## 3. Invoke

```
/<plugin>:<dir under skills/>
```

This repo today: `/release-please:setup`

## 4. Reload after edits

```
/reload-plugins
```

## Four things mistaken for bugs

- Plugin skills do **not** appear in `/skills`. Use `/plugin`.
- Entries in `/skills` without a colon are personal skills in `~/.claude/skills/`, unrelated to this repo.
- Without `--plugin-dir`, editing the working tree and running `/reload-plugins` does **nothing**. Committing does nothing either.
- Pushing to `main` ≠ users receive it. Bump `version` in `plugins/<name>/.claude-plugin/plugin.json`.

## Before committing

```bash
claude plugin validate ./plugins/<name>
```
