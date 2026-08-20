"""release-please 后端。

生成三个文件：
  - .github/workflows/release-please.yml
  - release-please-config.json
  - .release-please-manifest.json
"""

from deckhand.backends.base import Backend


class ReleasePleaseBackend(Backend):
    display_name = "release-please"

    def generate(self, config) -> dict[str, str]:
        """根据配置生成所有需要的文件内容。"""
        return {
            ".github/workflows/release-please.yml": self._workflow(),
            "release-please-config.json": self._config(config),
            ".release-please-manifest.json": self._manifest(config),
        }

    def _workflow(self) -> str:
        return 'on:\n  push:\n    branches:\n      - main\n\npermissions:\n  contents: write\n  pull-requests: write\n\nname: release-please\n\njobs:\n  release-please:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: googleapis/release-please-action@v4\n        with:\n          config-file: release-please-config.json\n          manifest-file: .release-please-manifest.json\n'

    def _config(self, config) -> str:
        return (
            '{\n'
            f'  "packages": {{\n'
            f'    ".": {{\n'
            f'      "release-type": "simple",\n'
            f'      "package-name": "{config.package_name}",\n'
            f'      "changelog-path": "{config.changelog_path}",\n'
            f'      "include-component-in-tag": false,\n'
            f'      "bump-minor-pre-major": true\n'
            f'    }}\n'
            f'  }},\n'
            f'  "$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json"\n'
            '}\n'
        )

    def _manifest(self, config) -> str:
        version = config.current_version
        return '{\n  ".": "' + version + '"\n}\n'
