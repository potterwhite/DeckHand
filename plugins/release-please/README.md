[English](README.md) | [中文](README.zh-CN.md)

# release-please

Set up [google/release-please](https://github.com/googleapis/release-please) semantic auto-releases
on any GitHub repo: prefix commits with `feat:` / `fix:`, and the bot computes the version, writes
`CHANGELOG.md`, opens a Release PR, creates the tag, and publishes the GitHub Release.

## 1. Skill

| Skill | Does |
|---|---|
| `/release-please:setup` | Configure the whole pipeline in the current repo |

## 2. Use

Not installed yet? See the [repo README](../../README.md#2-install).

Run it inside the **target repo**:

```
/release-please:setup
```

## 3. What it does

1. **Survey** — default branch, existing tags and releases, language ecosystem, conflicting files
2. **Agree on a version policy** — stops and asks you two questions; see Appendix 1
3. **Generate** — three files: the workflow, `release-please-config.json`, `.release-please-manifest.json`
4. **Commit and push** — on a new branch, stops for your confirmation
5. **Turn on the permission switch** — the only step needing repo admin, stops for your confirmation
6. **Verify** — check the first run, explain any failure

Nothing is written before step 2, and steps 4 and 5 each stop for you.

## 4. Prerequisites

| Needed | When | Without it |
|---|---|---|
| `git` + push access | throughout | cannot proceed |
| GitHub remote | throughout | unsupported — the action only runs on GitHub |
| repo admin | step 5 | someone with admin has to flip one switch |
| `gh` logged in | steps 1, 5, 6 | degrades to handing you links to click; nothing is lost |
| `workflow` token scope | step 4, **HTTPS remotes only** | the push is rejected; switch to SSH or run `gh auth refresh -h github.com -s workflow` |

---

Everything below is background — read it when a question comes up, not before.

## Appendix 1 · The two questions in step 2

Both are cheap to answer now and expensive to get wrong later.

**What is the current version?** It seeds `.release-please-manifest.json`. Seed it wrong and the next
release renumbers from a low version. Tags can lie — release branches, mistagged commits, tags that
never shipped — so the detected value is reported for you to confirm rather than assumed.

This does **not** hand version control back to you:

> The manifest is written once, by you, at init. After the first release the bot owns the file and
> rewrites it every time. Seeding the starting version is like setting an odometer's initial reading
> — CI still decides every bump from here.

**Should pre-1.0 guardrails go on?** Offered only below `1.0.0`. `bump-minor-pre-major` means
"breaking changes only bump semver minor if version < 1.0.0"; `bump-patch-for-minor-pre-major` means
"feature changes only bump semver patch if version < 1.0.0". Neither changes how commits are
interpreted — they only soften the outcome while the project is young.

If you ask to "only ever bump minor", the skill will push back rather than comply. The field that
literally does that, `versioning: always-bump-minor`, makes commit types meaningless — `fix:` bumps
minor, `feat!:` bumps minor — reducing release-please to a `+0.1.0` counter. Upstream documents
`always-bump-*` for backporting onto maintenance branches, not for the default branch. You will be
steered to the guardrails above, which is the tool that actually fits the intent; the override is
still written if you insist after hearing why.

## Appendix 2 · Why manifest mode

Manifest mode is what upstream calls "Manifest Driven release-please" and treats as the primary path.
From `release-please-action@v4` onward most action inputs were removed "in favor of manifest
configuration", so configuration lives in files, not in `with:` inputs. The generated workflow pins
`@v5`.

## Appendix 3 · Going deeper

`skills/setup/references/gotchas.md` — every claim carries a confidence figure, and anything that
could not be supported was deleted rather than hedged. Covers: the HTTPS `workflow` scope wall,
monorepos, syncing the version into source files with `extra-files`, writing values that only exist
at release time via `release_created`, branch protection conflicts, and PATs for triggering
downstream workflows.
