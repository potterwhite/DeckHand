# release-please 常见坑

## 0. workflow 文件推不上去（HTTPS remote 专属）

```
! [remote rejected] refusing to allow an OAuth App to create or update
  workflow `.github/workflows/release-please.yml` without `workflow` scope
```

GitHub 规定：**新建或修改 `.github/workflows/` 下的文件，token 必须带 `workflow` scope。**
`gh` 的默认 OAuth token 只有 `repo`，没有 `workflow`。而本 skill 唯一的产出就是一个
workflow 文件，所以这堵墙是必然会撞的 —— 但**只在 remote 是 HTTPS 时**。

**SSH 推送完全不受此限制**（SSH key 不是 OAuth token，没有 scope 概念）。
所以平时用 SSH 的人从没见过这个报错，一旦碰到某个 HTTPS remote 的仓库就懵了。

侦察阶段就该判断，别等 push 才炸：

```bash
git remote get-url origin        # git@ 或 ssh:// 开头 → 没问题
                                 # https:// 开头 → 继续查 scope
gh auth status 2>&1 | grep -i 'token scopes'
```

HTTPS 且缺 scope 时，两条解法：

1. **换成 SSH**（首选，无需重新授权）：
   ```bash
   git remote set-url origin git@github.com:OWNER/REPO.git
   ```
   多账号的人注意：`ssh -T git@github.com` 报的名字未必是你要的账号。用
   `~/.ssh/config` 里对应那个 alias，先 `ssh -T <alias>` 确认身份，再拿 alias 当 host：
   `git remote set-url origin <alias>:OWNER/REPO.git`

2. **给 token 补 scope**（需交互式浏览器授权，让用户自己跑）：
   ```bash
   gh auth refresh -h github.com -s workflow
   ```

### 两个连带的陷阱

**`pushurl` 会盖掉你的修改。** `git remote set-url origin <新地址>` 只改 fetch URL；
若仓库另配了 `remote.origin.pushurl`，push 仍走旧地址，报错一模一样，让人以为改了没用。
查 `git config --get-all remote.origin.pushurl`，或者干脆
`git remote remove origin && git remote add origin <新地址>` 一步到位。

**别把 `git push` 接管道。** `git push ... | tail` 的 `$?` 是 `tail` 的退出码，永远是 0，
失败会看起来像成功。而且 git 常在真正原因旁边额外吐一段 `Note about fast-forwards`
的 hint —— 那是误导，真原因在 `[remote rejected]` 那一行。

## 1. Actions 无法创建 PR（最高频）

报错 `GitHub Actions is not permitted to create or approve pull requests`。
仓库设置里的开关没开，见 SKILL.md 步骤 4。**无法**用 workflow 里的 `permissions:` 块代替。

## 2. 发版后下游 workflow 不触发

`GITHUB_TOKEN` 造出的事件不会触发其他 workflow。所以「发 release 后自动 publish」不会跑。
解法：建 PAT（`contents:write` + `pull_requests:write`），`gh secret set RELEASE_PLEASE_TOKEN`，
然后在 workflow 里加 `token: ${{ secrets.RELEASE_PLEASE_TOKEN }}`。

顺带的好处：用 PAT 就绕开了坑 1 那个开关。

## 3. 版本从 0.1.0 重新开始

release-please 优先看 GitHub **Releases**。只有 tag、没有对应 Release 时它可能找不到起点。
解法：改用 manifest 模式钉死版本，workflow 的 `with:` 换成

```yaml
          config-file: release-please-config.json
          manifest-file: .release-please-manifest.json
```

`release-please-config.json`：

```json
{ "packages": { ".": { "release-type": "python" } } }
```

`.release-please-manifest.json`（填当前真实版本）：

```json
{ ".": "1.4.2" }
```

## 4. 0.x 的 breaking change 直接跳到 1.0.0

默认行为。想留在 pre-1.0，在 config 的包配置里加：

```json
{ "packages": { ".": {
  "release-type": "python",
  "bump-minor-pre-major": true,
  "bump-patch-for-minor-pre-major": true
} } }
```

## 5. monorepo

必须用 manifest 模式，`packages` 里逐个列出；tag 需要区分时加 `"include-component-in-tag": true`。

```json
{ "packages": {
  "packages/api": { "release-type": "node" },
  "packages/cli": { "release-type": "node" }
} }
```

## 6. 版本号要同步进源文件

release-type 只改该生态的标准清单文件。版本在别处（如 `__init__.py`）时用 `extra-files`：

```json
{ "packages": { ".": {
  "release-type": "python",
  "extra-files": ["src/pkg/__init__.py"]
} } }
```

被改的文件里要标注：`# x-release-please-version`

## 7. 分支保护挡住 release PR

默认分支要求 review 或 status check 时，机器人的 PR 合不掉、tag 推不上。
要么给 bot 开 bypass，要么人工合并 release PR。
