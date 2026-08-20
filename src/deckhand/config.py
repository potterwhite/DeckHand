"""DeckHand 配置管理。"""

from dataclasses import dataclass


@dataclass
class DeckHandConfig:
    backend: str
    package_name: str
    current_version: str
    changelog_path: str = "CHANGELOG.md"
