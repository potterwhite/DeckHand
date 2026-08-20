"""DeckHand 配置管理。"""

from dataclasses import dataclass
from pathlib import Path

# release-please 支持的 release-type。`simple` 只在 manifest 里记版本号，
# 不会去改项目文件里的 version 字段 —— 对 Python/Node 包通常不是想要的行为。
RELEASE_TYPES = ("simple", "python", "node", "ruby", "terraform-module")


@dataclass
class DeckHandConfig:
    backend: str
    package_name: str
    current_version: str
    changelog_path: str = "CHANGELOG.md"
    release_type: str = "simple"
    bump_minor_pre_major: bool = True
    # 生成的 workflow 监听哪个分支的 push。写死 main 会让 master 仓库
    # 静默失效 —— workflow 装上了但永远不触发。
    default_branch: str = "main"

    def __post_init__(self) -> None:
        if self.release_type not in RELEASE_TYPES:
            raise ValueError(
                f"未知 release-type: {self.release_type}，"
                f"可选: {', '.join(RELEASE_TYPES)}"
            )


def detect_release_type(repo_root: Path) -> str:
    """按项目里的清单文件猜 release-type。

    这决定 release-please 会不会顺手把版本号写回项目文件：
      pyproject.toml → python，会更新 pyproject 里的 version
      package.json   → node，会更新 package.json 里的 version
      都没有          → simple，只维护 manifest 和 CHANGELOG

    猜错的代价是版本号不同步，所以 CLI 留了 --release-type 覆盖。
    """
    if (repo_root / "pyproject.toml").exists() or (repo_root / "setup.py").exists():
        return "python"
    if (repo_root / "package.json").exists():
        return "node"
    return "simple"


def changelog_looks_managed(path: Path) -> bool:
    """判断已存在的 CHANGELOG 是否像 release-please 生成的。

    release-please 会接管 CHANGELOG.md 并按自己的格式往里写。如果那是
    一份手写的 changelog，直接交给它就等于把人写的内容混进机器格式里。
    这里用来决定要不要停下来问用户。

    识别特征：release-please 的条目形如
        ## [1.2.3](https://github.com/o/r/compare/v1.2.2...v1.2.3) (2026-01-01)
    """
    if not path.exists():
        return True  # 不存在 → 没有冲突风险
    try:
        head = path.read_text(encoding="utf-8", errors="replace")[:4000]
    except OSError:
        return False
    return "/compare/" in head and "## [" in head
