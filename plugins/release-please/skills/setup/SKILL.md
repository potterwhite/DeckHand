---
name: setup
description: Configure a google/release-please automated release pipeline for a GitHub repo — survey the repo, agree on a version policy, generate the manifest-mode config, walk through the required permission switch, verify the first run. Use when the user asks to "set up automated releases", "init release-please", "setup CI release", "add automatic changelog", "automate versioning", or 配置自动发版 / 初始化 release-please / 自动生成 changelog / 自动升版本号.
allowed-tools: Read, Glob, Bash(git rev-parse *), Bash(git remote *), Bash(git tag *), Bash(git describe *), Bash(git log *), Bash(git status *), Bash(git branch *), Bash(gh repo view *), Bash(gh release list *), Bash(gh auth status)
---

# release-please setup

Set up automated releases in the **target repo** — the repo the user is currently in, not DeckHand
itself.

This skill uses **manifest mode** (`release-please-config.json` + `.release-please-manifest.json`),
which is what upstream calls "Manifest Driven release-please" and treats as the primary path.
From `release-please-action@v4` onward most action inputs were removed "in favor of manifest
configuration", so config files — not `with:` inputs — are where configuration belongs.

## Hard rules

1. Stop for user confirmation before pushing, and before changing repo settings.
2. Never silently overwrite an existing `.github/workflows/release*.yml`, `release-please-config.json`,
   `.release-please-manifest.json`, or `CHANGELOG.md` — report and ask.
3. Stop if the remote is not GitHub: `release-please-action` only runs on GitHub.
4. **Never guess the initial version.** Getting it wrong makes the next release renumber from
   `0.1.0`. Confirm it with the user in step 2.

## Step 1 · Survey

```bash
git remote get-url origin                                 # GitHub? owner/repo?
git remote show origin | sed -n 's/.*HEAD branch: //p'    # default branch
git describe --tags --abbrev=0 2>/dev/null                # current version, if any
git tag --sort=-v:refname | head -5                       # tag naming pattern
gh release list --limit 5                                 # do Releases exist? any drafts?
ls .github/workflows/ CHANGELOG.md 2>/dev/null            # conflicts
gh repo view --json viewerPermission -q .viewerPermission # ADMIN? decides step 5's path
gh auth status 2>&1 | grep -i 'token scopes'              # only matters for https:// remotes
```

**Do not use `git symbolic-ref refs/remotes/origin/HEAD` to find the default branch** — that ref is
unset in many repos and fails with `fatal: ref ... is not a symbolic ref`. Use the `git remote show`
line above, or `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`.

**If the remote is `https://` and the token scopes do not include `workflow`, stop now and tell the
user.** This skill writes into `.github/workflows/`, and GitHub refuses that write from an OAuth
token lacking `workflow` scope — the push in step 4 will be rejected. SSH remotes are exempt.
Fix: [references/gotchas.md](references/gotchas.md) § 0.

Pick `release-type` from the manifest file in the repo root:

| Found | release-type |
|---|---|
| `package.json` | `node` |
| `pyproject.toml` / `setup.py` | `python` |
| `Cargo.toml` | `rust` |
| `go.mod` | `go` |
| `pom.xml` | `maven` |
| `composer.json` | `php` |
| `*.gemspec` | `ruby` |
| none of the above | `simple` |

## Step 2 · Agree on the version policy (stop and ask)

Report what step 1 found, then confirm two things with the user.

**(a) The starting version.** State the detected value and ask whether it is really the current
released version — tags can lie (release branches, mistagged commits, tags that never shipped).

Reassure them about what this does and does not mean:

> `.release-please-manifest.json` is written **once, by you, at init**. After the first release the
> bot owns the file and rewrites it every time. Pinning the starting version does **not** take
> automatic version decisions away from CI — it is like setting an odometer's initial reading.

If no tags and no releases exist, use `0.0.0`.

**(b) Whether to add pre-1.0 guardrails.** Only offer these when the version is below `1.0.0`; they
do not alter semantic version computation, they only soften it while the project is young:

| Config field | Upstream meaning |
|---|---|
| `bump-minor-pre-major: true` | "Breaking changes only bump semver minor if version < 1.0.0" — won't jump to `1.0.0` |
| `bump-patch-for-minor-pre-major: true` | "Feature changes only bump semver patch if version < 1.0.0" — more conservative |

**If the user asks to "only ever bump minor" or otherwise wants to cap version movement, do not
reach for the `versioning` field.** Setting `versioning: always-bump-minor` makes commit types
meaningless — `fix:` bumps minor, `feat!:` bumps minor — which turns release-please into a
`+0.1.0` counter and throws away the reason to use it. Upstream documents `always-bump-patch` for
**backporting fixes to a maintenance branch**, not for day-to-day releases on the default branch.
Explain this, and steer them to the pre-1.0 guardrails above, which is the tool that actually fits
that intent. Only write a `versioning` override if they still insist after hearing the tradeoff.

## Step 3 · Generate the three files

Read each template from `${CLAUDE_SKILL_DIR}/templates/`, substitute, and write to the target repo:

| Template | Written to | Substitutions |
|---|---|---|
| `release-please.yml` | `.github/workflows/release-please.yml` | `__DEFAULT_BRANCH__` |
| `release-please-config.json` | `release-please-config.json` | `__RELEASE_TYPE__` |
| `.release-please-manifest.json` | `.release-please-manifest.json` | `__INITIAL_VERSION__` |

Add any guardrail fields agreed in step 2 into the `"."` package block of the config.

The workflow pins `googleapis/release-please-action@v5`. `v5.0.0` (2026-04-22) shipped exactly one
breaking change — a **Node 24 runtime**. Config format is unchanged from v4. If the repo uses
**self-hosted runners** too old for Node 24, drop to `@v4`; nothing else needs to change.

For monorepos, syncing the version into source files, or writing values that only exist at release
time, read [references/gotchas.md](references/gotchas.md).

## Step 4 · Commit and push (stop and confirm)

Commit on a new branch. Do not push straight to the default branch.

**Never pipe `git push`.** `git push | tail` exits with `tail`'s status — always 0 — so a rejected
push looks like a success. When it is rejected, read the `[remote rejected]` line; ignore the
`Note about fast-forwards` hint printed next to it, which is usually about a different problem.

## Step 5 · Turn on the permission switch (stop and confirm)

**The one action in this whole flow that needs repo admin.** Without it release-please cannot create
its Release PR. The `permissions:` block inside the workflow yaml does **not** substitute for it —
they are different layers.

With `gh` available and authenticated:

```bash
gh api -X PUT repos/OWNER/REPO/actions/permissions/workflow \
  -f default_workflow_permissions=write \
  -F can_approve_pull_request_reviews=true
```

Otherwise hand the user the link and have them tick
**Allow GitHub Actions to create and approve pull requests**, then Save:

```
https://github.com/OWNER/REPO/settings/actions
```

## Step 6 · Verify after merge

Merge the config branch into the default branch → the workflow runs.

release-please scans "commits since the last release". If history already contains `feat:` / `fix:`
commits it opens a Release PR immediately. **Only fabricate a trigger commit when there is not a
single conventional commit to work from** — do not reflexively create one.

```bash
gh run list --workflow=release-please.yml --limit 3
gh pr list --label "autorelease: pending"
```

The bot's PR is titled like `chore(main): release 0.6.0`. Merging it creates the tag, publishes the
GitHub Release, and writes `CHANGELOG.md`.

`GitHub Actions is not permitted to create or approve pull requests` means step 5 was skipped.
Anything else: [references/gotchas.md](references/gotchas.md).

## Commit convention

`feat:` → minor. `fix:` → patch. `feat!:` or `BREAKING CHANGE:` in the body → major (minor instead
when `bump-minor-pre-major` is on and the version is below `1.0.0`). `chore:` / `docs:` / `refactor:`
/ `test:` / `style:` → no release.

A `Release-As: 2.0.0` footer in the commit body forces a specific version. Do **not** use the
`release-as` config field — upstream has deprecated it in favor of that footer.

On squash merge release-please reads the **PR title**, so the PR title is what must be conventional.
