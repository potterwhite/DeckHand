# release-please gotchas

Each item carries a **confidence** figure. It is not decoration — read it as follows:

| Confidence | Basis |
|---|---|
| **100%** | Quoted from upstream docs, or structurally certain (e.g. how a shell exit code works) |
| **90–95%** | Upstream docs plus a short inference, or a behaviour verified in practice |
| **70–85%** | Reasoned from documented mechanism, not itself documented. Treat as likely, verify if it matters |
| **below 70%** | **Deleted rather than hedged.** Claims that could not be supported are not in this file |

A previous revision of this file asserted that release-please "looks at GitHub Releases before tags".
That could not be substantiated against upstream documentation and has been removed, not downgraded.
Where the *mechanism* is unclear but the *fix* is known, only the fix is documented below.

---

## 0. Workflow file cannot be pushed (HTTPS remotes only)

```
! [remote rejected] refusing to allow an OAuth App to create or update
  workflow `.github/workflows/release-please.yml` without `workflow` scope
```

**Confidence: 100%** — GitHub requires the `workflow` OAuth scope to create or modify anything under
`.github/workflows/`. This skill's whole output lives there, so the wall is unavoidable when it
applies.

**Confidence: 100%** — **SSH pushes are exempt.** An SSH key is not an OAuth token and has no scopes
at all. This is why people who normally use SSH have never seen the error and are baffled the first
time they hit an HTTPS remote.

**Confidence: 75%** — whether a given `gh` token carries `workflow` varies by `gh` version and by
which login flow was used. **Check, do not assume either way:**

```bash
git remote get-url origin        # git@ or ssh:// → no problem
                                 # https:// → check scopes
gh auth status 2>&1 | grep -i 'token scopes'
```

Two fixes when the remote is HTTPS and the scope is absent:

1. **Switch to SSH** (preferred — no re-authorization needed):
   ```bash
   git remote set-url origin git@github.com:OWNER/REPO.git
   ```
   **Confidence: 90%** — with multiple accounts, the name reported by `ssh -T git@github.com` is not
   necessarily the account you want. Use the matching alias from `~/.ssh/config`, confirm identity
   with `ssh -T <alias>`, then use the alias as the host:
   `git remote set-url origin <alias>:OWNER/REPO.git`

2. **Add the scope to the token** (needs interactive browser authorization — have the user run it):
   ```bash
   gh auth refresh -h github.com -s workflow
   ```

### Two traps that ride along

**Confidence: 95%** — **`pushurl` silently overrides your fix.** `git remote set-url origin <new>`
changes only the fetch URL. If the repo also has `remote.origin.pushurl` configured, pushes still go
to the old address and the error is identical, making the fix look ineffective. Check
`git config --get-all remote.origin.pushurl`, or sidestep it entirely with
`git remote remove origin && git remote add origin <new>`.

**Confidence: 100%** — **never pipe `git push`.** In `git push ... | tail`, `$?` is `tail`'s exit
code, which is always 0, so a failure looks like a success. Separately, git often prints a
`Note about fast-forwards` hint next to the real cause; that hint is usually misleading — the real
reason is on the `[remote rejected]` line.

## 1. Actions cannot create the PR (most frequent)

```
GitHub Actions is not permitted to create or approve pull requests
```

**Confidence: 100%** — the repository setting is off. See SKILL.md step 5.

**Confidence: 95%** — this **cannot** be substituted with the `permissions:` block in the workflow
yaml. They are different layers: the repo setting governs whether Actions may open PRs at all, while
`permissions:` only scopes the token within a run. Granting `pull-requests: write` in the yaml does
not help if the repo switch is off.

## 2. Downstream workflows do not trigger after a release

**Confidence: 100%** — events created using `GITHUB_TOKEN` do not trigger further workflow runs.
So "publish automatically after a release is created" will not fire.

**Confidence: 90%** — fix: create a PAT with `contents:write` + `pull_requests:write`, store it, and
pass it to the action:

```bash
gh secret set RELEASE_PLEASE_TOKEN
```

```yaml
      - uses: googleapis/release-please-action@v5
        with:
          token: ${{ secrets.RELEASE_PLEASE_TOKEN }}
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json
```

**Confidence: 80%** — side benefit: a PAT acts as a user rather than as `GITHUB_TOKEN`, so it is not
governed by the repo switch in gotcha 1. Reasoned from how that setting is scoped, not stated
upstream — verify before relying on it as the *only* fix.

## 3. Version restarts from a low number

**Confidence: 95%** — in manifest mode, `.release-please-manifest.json` is the record of the last
released version. If it is missing, or seeded with a value that does not match reality, the next
release is computed from the wrong base. Seed it with the real current version at init:

```json
{ ".": "1.4.2" }
```

**Confidence: 100%** — the CLI has a flag for exactly this. Upstream describes `--initial-version` as
"Version string to set as the last released version of this package. Defaults to `0.0.0`."

```bash
npx release-please bootstrap \
  --token="$(gh auth token)" \
  --repo-url=OWNER/REPO \
  --release-type=simple \
  --initial-version=1.4.2
```

**Confidence: 95%** — one concrete cause of a lost starting point is **draft releases**. Upstream
documents `--force-tag-creation` precisely because "GitHub does not create a Git tag for draft
releases until they are published", which leaves release-please unable to find the previous release.
Either publish the release or pass that flag.

**Confidence: 95%** — after the first successful run the **bot owns the manifest** and rewrites it on
every release. Seeding it is a one-time initialization, not an ongoing override, and it does not take
version decisions away from CI.

## 4. A breaking change in 0.x jumps straight to 1.0.0

**Confidence: 100%** — that is the default. Both guardrail fields are quoted from upstream:

| Field | Upstream wording |
|---|---|
| `bump-minor-pre-major` | "Breaking changes only bump semver minor if version < 1.0.0" |
| `bump-patch-for-minor-pre-major` | "Feature changes only bump semver patch if version < 1.0.0" |

```json
{ "packages": { ".": {
  "release-type": "python",
  "bump-minor-pre-major": true,
  "bump-patch-for-minor-pre-major": true
} } }
```

## 5. Do not cap versions with `versioning`

**Confidence: 100%** — the six strategies upstream offers:

| Strategy | Behaviour |
|---|---|
| `default` | breaking → major, feature → minor, fix → patch |
| `always-bump-patch` | always patch |
| `always-bump-minor` | always minor |
| `always-bump-major` | always major |
| `service-pack` | Java backports, `1.2.3-sp.1` shape |
| `prerelease` | increments the prerelease number; pair with `prerelease: true` |

**Confidence: 100%** — `always-bump-*` makes commit types irrelevant: with `always-bump-minor`,
`fix:` bumps minor and `feat!:` bumps minor. That reduces release-please to a `+0.1.0` counter and
discards the reason to run it.

**Confidence: 95%** — upstream documents `always-bump-patch` for **backporting fixes onto a
maintenance branch**, not for routine releases on the default branch. When a user wants to "stay in
0.x", gotcha 4 is the correct tool, not this field.

**Confidence: 95%** — naming trap: the **action input** is `versioning-strategy` while the
**config field** is `versioning`. Copying one name into the other position silently does nothing.

## 6. Forcing a specific version

**Confidence: 100%** — put a footer in the commit body:

```
Release-As: 2.0.0
```

**Confidence: 100%** — do **not** use the `release-as` config field. Upstream marks it DEPRECATED
with the note "Consider using a `Release-As` commit instead."

## 7. Monorepo

**Confidence: 95%** — list every package under `packages`. Multi-package releases need the manifest
config; there is no way to express a package map through action inputs.

```json
{ "packages": {
  "packages/api": { "release-type": "node" },
  "packages/cli": { "release-type": "node" }
} }
```

**Confidence: 95%** — set `"include-component-in-tag": true` when tags must distinguish packages
(producing `api-v1.2.3`). Keep it `false` for a single-package repo, otherwise tags gain a prefix
nothing else expects.

## 8. Syncing the version into source files

**Confidence: 95%** — `release-type` only updates that ecosystem's standard manifest file
(`package.json`, `Cargo.toml`, …). For a version stored anywhere else, declare the file:

```json
{ "packages": { ".": {
  "release-type": "python",
  "extra-files": ["VERSION", "src/pkg/__init__.py"]
} } }
```

**Confidence: 95%** — declaring is not enough; the target file must carry a marker. The inline
keywords:

| Keyword | Replaced with |
|---|---|
| `x-release-please-version` | full version, `1.7.0` |
| `x-release-please-major` | `1` |
| `x-release-please-minor` | `7` |
| `x-release-please-patch` | `0` |

Inline — replaces the value on that line only:

```python
__version__ = "1.7.0"  # x-release-please-version
```

Block — every version-looking value between the markers is replaced:

```yaml
# x-release-please-start-version
version: 1.7.0
image: myapp:1.7.0
# x-release-please-end
```

**Confidence: 95%** — structured formats can target a path instead of needing a comment marker:

```json
{ "extra-files": [
  { "type": "json", "path": "app/config.json", "jsonpath": "$.version" },
  { "type": "yaml", "path": "chart/Chart.yaml", "jsonpath": "$.appVersion" },
  { "type": "toml", "path": "conf/app.toml",   "jsonpath": "$.package.version" },
  { "type": "xml",  "path": "pom.xml",         "xpath": "//project/version" },
  { "type": "generic", "path": "notes.md" }
] }
```

## 9. Writing values that only exist at release time

**Confidence: 100%** — release-please cannot write a release date. Its model is *open a PR now, wait
for a merge later*; when it composes the PR it does not know when that merge will happen. Anything
whose value is only determined at release time has to be handled in the workflow.

**Confidence: 95%** — the pattern below has been verified working in practice. It hangs off the
action's `release_created` output:

```yaml
jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v5
        id: release
        with:
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json

      - uses: actions/checkout@v4
        if: ${{ steps.release.outputs.release_created }}

      - name: Write the release date
        if: ${{ steps.release.outputs.release_created }}
        run: |
          RELEASE_DATE=$(date -u +"%Y-%m-%d")
          sed -i "s/^PROJECT_RELEASE_DATE=.*/PROJECT_RELEASE_DATE=${RELEASE_DATE}/" \
            configs/common.env
          git config user.name  "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"
          git add configs/common.env
          git commit -m "chore: set release date ${RELEASE_DATE} for ${{ steps.release.outputs.tag_name }}"
          git push
```

Why each piece is there:

| Piece | Reason | Confidence |
|---|---|---|
| `id: release` | Without an id there is no way to reference `steps.release.outputs` | 100% |
| `if: steps.release.outputs.release_created` | This workflow runs on *every* push to the default branch; the output is only true when a Release PR was merged, so ordinary commits skip these steps | 95% |
| `date -u` | UTC matches the GitHub Release timestamp, avoiding timezone ambiguity | 100% |
| `sed "s/^KEY=.*/"` matching the whole line | Idempotent — overwrites correctly whether the previous value was empty or a stale date | 100% |
| `chore:` commit prefix | `chore` does not trigger a release, so this push does not make release-please open another Release PR — it avoids a loop | 95% |
| `github-actions[bot]` identity | Standard bot identity, keeps automated commits distinguishable from human ones | 100% |

## 10. Branch protection blocks the release PR

**Confidence: 90%** — when the default branch requires reviews or passing status checks, the bot's
Release PR cannot be merged. Either grant the bot a bypass, or merge the Release PR manually.

**Confidence: 70%** — tag protection rules, if configured, can additionally block tag creation after
the merge. Reasoned from how tag protection works rather than observed here; check tag rules only if
the merge succeeds but no tag appears.
