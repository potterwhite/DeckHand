"""release-please 后端。

生成三个文件：
  - .github/workflows/release-please.yml
  - release-please-config.json
  - .release-please-manifest.json

两处和早期版本的关键差异：

1. action 从 v4 升到 v5。v5.0.0 唯一的 breaking change 是 runtime 升到
   Node 24（GitHub 托管的 ubuntu-latest 自带），`config-file` 和
   `manifest-file` 两个入参在 v5 的 action.yml 里都还在，已核对。

2. workflow 里加了 workflow_dispatch。这样触发首次发版只要
   `gh workflow run` 就行 —— 早期做法是往仓库里塞一个空的
   TRIGGER_RELEASE.md 再造一个假的 `feat:` commit，会留下垃圾文件
   和一个没有意义的 release。
"""

import json

from deckhand.backends.base import Backend

WORKFLOW_FILENAME = "release-please.yml"
WORKFLOW_PATH = f".github/workflows/{WORKFLOW_FILENAME}"
CONFIG_PATH = "release-please-config.json"
MANIFEST_PATH = ".release-please-manifest.json"

_SCHEMA = (
    "https://raw.githubusercontent.com/googleapis/release-please"
    "/main/schemas/config.json"
)


class ReleasePleaseBackend(Backend):
    display_name = "release-please"

    def generate(self, config) -> dict[str, str]:
        """根据配置生成所有需要的文件内容。"""
        return {
            WORKFLOW_PATH: self._workflow(config),
            CONFIG_PATH: self._config(config),
            MANIFEST_PATH: self._manifest(config),
        }

    def _workflow(self, config) -> str:
        branch = getattr(config, "default_branch", "main") or "main"
        return f"""name: release-please

on:
  push:
    branches:
      - {branch}
  workflow_dispatch:

permissions:
  contents: write
  pull-requests: write

jobs:
  release-please:
    runs-on: ubuntu-latest
    steps:
      - uses: googleapis/release-please-action@v5
        with:
          config-file: {CONFIG_PATH}
          manifest-file: {MANIFEST_PATH}
"""

    def _config(self, config) -> str:
        """用 json.dumps 生成，而不是手拼字符串。

        手拼的版本在 package_name 含引号或反斜杠时会生成语法错误的 JSON，
        而这个文件是 CI 读的 —— 坏了要等到 workflow 跑起来才发现。
        """
        payload = {
            "$schema": _SCHEMA,
            "packages": {
                ".": {
                    "release-type": config.release_type,
                    "package-name": config.package_name,
                    "changelog-path": config.changelog_path,
                    "include-component-in-tag": False,
                    "bump-minor-pre-major": config.bump_minor_pre_major,
                }
            },
        }
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"

    def _manifest(self, config) -> str:
        payload = {".": config.current_version}
        return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
