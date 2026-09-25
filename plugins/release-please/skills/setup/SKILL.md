---
name: setup
description: Configure a google/release-please automated release pipeline for a GitHub repo — survey the repo, agree on a version policy, generate the manifest-mode config, walk through the required repo settings (Actions permissions, branch protection), verify the first run. Use when the user asks to "set up automated releases", "init release-please", "setup CI release", "add automatic changelog", "automate versioning", or 配置自动发版 / 初始化 release-please / 自动生成 changelog / 自动升版本号.
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
gh repo view --json viewerPermission -q .viewerPermission # ADMIN? decides step 4's path
gh auth status 2>&1 | grep -i 'token scopes'              # only matters for https:// remotes
command -v gh                                             # missing? step 4 offers to install it
gh api repos/OWNER/REPO/branches/BRANCH/protection        # 404 = unprotected; feeds step 4
```

**Do not use `git symbolic-ref refs/remotes/origin/HEAD` to find the default branch** — that ref is
unset in many repos and fails with `fatal: ref ... is not a symbolic ref`. Use the `git remote show`
line above, or `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`.

**If the remote is `https://` and the token scopes do not include `workflow`, stop now and tell the
user.** This skill writes into `.github/workflows/`, and GitHub refuses that write from an OAuth
token lacking `workflow` scope — the push in step 5 will be rejected. SSH remotes are exempt.
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

## Step 4 · Repo settings: protection + permissions (stop and confirm)

Three switches that live in the repo's GitHub settings, not in the files you just generated.
All three need **repo admin**. Do this before the push in step 5 so that everything is in
place when the config PR later merges.

**Ask first, with the full picture.** Present exactly this list (in the user's language),
then AskUserQuestion:

> Turn on these 3 settings?
>
> **1. Actions default write permission** (`default_workflow_permissions=write`)
> What it does: lets workflows write to the repo — needed to create tags and publish
> Releases.
> Manual path: github.com → your repo → Settings → Actions → General →
> "Workflow permissions" → select "Read and write permissions" → Save
>
> **2. Let Actions create and approve pull requests** (`can_approve_pull_request_reviews=true`)
> What it does: without it release-please can never open its Release PR.
> Manual path: same page as setting 1 → tick
> "Allow GitHub Actions to create and approve pull requests" → Save
>
> **3. Protect the default branch** (PR required, force-push and deletion blocked)
> What it does: the default branch can no longer be pushed to directly, force-pushed, or
> deleted. release-please is unaffected — it only opens PRs, and the tag is created when
> a human merges the Release PR.
> Manual path: github.com → your repo → Settings → Branches →
> "Add branch protection rule" → branch name pattern `main` → tick
> "Require a pull request before merging" (leave required approvals at 0) → Create
>
> Web paths are GitHub's own UI and may change; the on-screen page is authoritative.

**If the user declines: respect it, do not argue.** Print this once and skip the rest of
the step:

> Skipped. Consequences:
> - Without 1+2, the first workflow run fails with `GitHub Actions is not permitted to
>   create or approve pull requests` — no Release PR, ever
>   ([references/gotchas.md](references/gotchas.md) § 1).
> - Without 3, the default branch stays open to direct pushes, force-push, and deletion.

### gh must exist and be logged in

`command -v gh` — if missing, look up the install command for the user's platform from the
official GitHub CLI docs, then AskUserQuestion ("Install gh? The command is: …"), print the
command, and run it only on a yes. If `gh auth status` shows no login, ask the user to run
`gh auth login` themselves — it is interactive and cannot be done for them.

No gh, or no admin on the repo → hand the user the three manual paths above and move on.
Nothing else in this skill depends on this step.

### Apply one command at a time

For each command: print it, AskUserQuestion, run it only on a yes.

**Settings 1+2** — one command sets both fields:

```bash
gh api -X PUT repos/OWNER/REPO/actions/permissions/workflow \
  -f default_workflow_permissions=write \
  -F can_approve_pull_request_reviews=true
```

The `permissions:` block inside the workflow yaml does **not** substitute for this — they
are different layers (gotchas § 1).

**Setting 3** — step 1 already fetched the current protection state. **Report what exists
and ask before changing it; never silently overwrite.** Offer tiers:

- **basic (recommended)** — PR required with 0 approvals, force-push off, deletion off,
  `enforce_admins: false` so a solo admin keeps a back door:

```bash
gh api -X PUT repos/OWNER/REPO/branches/BRANCH/protection --input - <<'EOF'
{
  "required_status_checks": null,
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF
```

- **strict** — basic + 1 approving review + linear history. Warn first: the bot cannot
  approve its own Release PR, so every release then needs a human merge or an admin bypass
  ([references/gotchas.md](references/gotchas.md) § 10).
- **skip** — leave the branch unprotected (the decline warning above already said what
  that means).

## Step 5 · Commit and push (stop and confirm)

Commit on a new branch. Do not push straight to the default branch.

**Never pipe `git push`.** `git push | tail` exits with `tail`'s status — always 0 — so a rejected
push looks like a success. When it is rejected, read the `[remote rejected]` line; ignore the
`Note about fast-forwards` hint printed next to it, which is usually about a different problem.

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

`GitHub Actions is not permitted to create or approve pull requests` means step 4 was skipped.
Anything else: [references/gotchas.md](references/gotchas.md).

## Commit convention

`feat:` → minor. `fix:` → patch. `feat!:` or `BREAKING CHANGE:` in the body → major (minor instead
when `bump-minor-pre-major` is on and the version is below `1.0.0`). `chore:` / `docs:` / `refactor:`
/ `test:` / `style:` → no release.

A `Release-As: 2.0.0` footer in the commit body forces a specific version. Do **not** use the
`release-as` config field — upstream has deprecated it in favor of that footer.

On squash merge release-please reads the **PR title**, so the PR title is what must be conventional.
