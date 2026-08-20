"""
DeckHand CLI 入口。

使用方式:
    python -m deckhand setup          # 在当前目录初始化 release-please
    python -m deckhand setup --backend changesets  # 指定后端
    python -m deckhand status         # 检查当前仓库的发版配置状态
    python -m deckhand ship           # 触发一次发版流程
"""

import argparse
import sys
from pathlib import Path

from deckhand.backends import get_backend, list_backends
from deckhand.config import DeckHandConfig
from deckhand.git import get_current_version, is_git_repo


def cmd_setup(args: argparse.Namespace) -> None:
    """初始化发版配置。"""
    repo_root = Path.cwd()

    if not is_git_repo(repo_root):
        print("错误: 当前目录不是 git 仓库", file=sys.stderr)
        sys.exit(1)

    current_version = get_current_version(repo_root)
    print(f"当前版本: {current_version or '无（将使用 0.0.0）'}")

    backend = get_backend(args.backend)
    config = DeckHandConfig(
        backend=args.backend,
        package_name=args.package_name or repo_root.name,
        current_version=current_version or "0.0.0",
        changelog_path=args.changelog_path or "CHANGELOG.md",
    )

    print(f"\n后端: {backend.display_name}")
    print(f"包名: {config.package_name}")
    print(f"CHANGELOG: {config.changelog_path}")
    print(f"\n生成配置文件...")

    files = backend.generate(config)
    for filepath, content in files.items():
        target = repo_root / filepath
        target.write_text(content)
        print(f"  已生成: {filepath}")

    print("\n下一步:")
    print("  1. git add . && git commit -m 'chore: bootstrap release-please'")
    print("  2. git push --set-upstream origin <配置分支名>")
    print("  3. 在 GitHub Settings → Actions 中开启 'Allow GitHub Actions to create and approve PRs'")
    print("  4. 合并配置分支到 main")
    print("  5. 用 'feat: ...' 提交一个功能 PR，合并后触发第一次发版")


def cmd_status(args: argparse.Namespace) -> None:
    """检查当前仓库的发版配置状态。"""
    repo_root = Path.cwd()

    if not is_git_repo(repo_root):
        print("错误: 当前目录不是 git 仓库", file=sys.stderr)
        sys.exit(1)

    # 检查常见配置文件是否存在
    checks = {
        ".github/workflows/release-please.yml": "GitHub Actions workflow",
        "release-please-config.json": "Release Please 配置",
        ".release-please-manifest.json": "版本清单",
        "CHANGELOG.md": "变更日志",
    }

    print(f"仓库: {repo_root.name}\n")
    for filepath, desc in checks.items():
        exists = (repo_root / filepath).exists()
        status = "已存在" if exists else "缺失"
        print(f"  [{status}] {desc} ({filepath})")

    current_version = get_current_version(repo_root)
    print(f"\n  当前版本: {current_version or '无 tag'}")


def cmd_ship(args: argparse.Namespace) -> None:
    """触发一次发版流程（通常由 CI 自动完成，此命令用于手动触发）。"""
    print("ship 命令即将支持手动触发 release-please PR 创建")
    print("当前请直接在 GitHub 上合并 release-please 的 Release PR 来完成发版")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="deckhand",
        description="DeckHand - CI 自动化的甲板水手",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # setup
    setup_parser = subparsers.add_parser("setup", help="初始化发版配置")
    setup_parser.add_argument(
        "--backend",
        default="release-please",
        choices=list_backends(),
        help="发版后端 (默认: release-please)",
    )
    setup_parser.add_argument("--package-name", help="包名（默认: 仓库名）")
    setup_parser.add_argument("--changelog-path", help="CHANGELOG 文件路径")

    # status
    subparsers.add_parser("status", help="检查当前配置状态")

    # ship
    subparsers.add_parser("ship", help="触发发版流程")

    args = parser.parse_args()

    if args.command == "setup":
        cmd_setup(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "ship":
        cmd_ship(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
