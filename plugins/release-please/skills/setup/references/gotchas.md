# release-please 常见坑

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
