"""
DeckHand CLI 入口。

使用方式:
    deckhand setup                    # 只生成配置文件（安全，不推不改设置）
    deckhand setup --auto             # 全自动：生成 → 推 → 开权限 → 合并 → 触发 → 验证
    deckhand setup --auto --dry-run   # 打印会执行什么，不执行
    deckhand status                   # 检查本地配置 + 远端 workflow 权限
    deckhand ship                     # 触发一次发版并等结果
"""

import argparse
import sys
from pathlib import Path

from deckhand import git, github, pipeline
from deckhand.backends import get_backend, list_backends
from deckhand.backends.release_please import WORKFLOW_FILENAME
from deckhand.config import (
    RELEASE_TYPES,
    DeckHandConfig,
    changelog_looks_managed,
    detect_release_type,
)


def _resolve_repo() -> Path:
    """定位仓库根目录，不在仓库里就退出。"""
    root = git.find_repo_root(Path.cwd())
    if root is None:
        print("错误: 当前目录不在任何 git 仓库内", file=sys.stderr)
        raise SystemExit(1)
    return root


def _build_config(repo_root: Path, args: argparse.Namespace) -> DeckHandConfig:
    current_version = git.get_current_version(repo_root)
    if current_version is None:
        print("当前版本: 无 tag（起始版本使用 0.0.0）")
    else:
        print(f"当前版本: {current_version}")

    release_type = args.release_type or detect_release_type(repo_root)
    if not args.release_type:
        print(f"release-type: {release_type}（自动探测，可用 --release-type 覆盖）")

    # 包名优先用远端仓库名，而不是本地目录名 —— 目录被改过名时两者会不一致。
    package_name = args.package_name or git.get_repo_name(repo_root)

    return DeckHandConfig(
        backend=args.backend,
        package_name=package_name,
        current_version=current_version or "0.0.0",
        changelog_path=args.changelog_path or "CHANGELOG.md",
        release_type=release_type,
        default_branch=args.base or git.default_branch(repo_root),
    )


def cmd_setup(args: argparse.Namespace) -> None:
    repo_root = _resolve_repo()
    config = _build_config(repo_root, args)
    backend = get_backend(config.backend)

    print(f"\n后端: {backend.display_name}")
    print(f"包名: {config.package_name}")
    print(f"CHANGELOG: {config.changelog_path}")
    print(f"默认分支: {config.default_branch}")

    files = backend.generate(config)

    if not args.auto:
        # 默认行为：只写文件。不推、不改仓库设置。
        print("\n生成配置文件...")
        for filepath, content in files.items():
            target = repo_root / filepath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            print(f"  已生成: {filepath}")

        changelog = repo_root / config.changelog_path
        if changelog.exists() and not changelog_looks_managed(changelog):
            print(
                f"\n注意: {config.changelog_path} 已存在且不是 release-please 格式。"
                "\n      合并后它会被接管并改写格式，建议先备份改名。"
            )

        print("\n只生成了文件，没有推送、没有改仓库设置。")
        print("要一步跑完剩下的流程: deckhand setup --auto")
        print("先看它会做什么:       deckhand setup --auto --dry-run")
        return

    # --auto
    try:
        if args.dry_run:
            # dry-run 也做预检 —— 提前暴露权限不足、CHANGELOG 冲突这类问题，
            # 免得用户看完计划才发现根本跑不了。
            try:
                info = pipeline.check_preconditions(
                    repo_root,
                    config,
                    allow_changelog_takeover=args.allow_changelog_takeover,
                )
                slug = info["nameWithOwner"]
                print(f"\n预检通过（{slug}，你的权限 {info.get('viewerPermission')}）\n")
            except pipeline.PipelineHalt as halt:
                slug = "<owner>/<repo>"
                print(f"\n预检未通过:\n{halt}\n")
                print("以下是预检通过后原本会执行的动作：\n")
            print(pipeline.build_plan(config, slug, list(files)).render())
            print("\n--dry-run: 什么都没有执行。")
            return

        info = pipeline.check_preconditions(
            repo_root,
            config,
            allow_changelog_takeover=args.allow_changelog_takeover,
        )
        print(f"\n目标仓库: {info['nameWithOwner']}\n")
        result = pipeline.run_auto(repo_root, config, files, info=info)

        print("\n完成。")
        if result.get("release_pr"):
            print(f"  Release PR: {result['release_pr']['url']}")
            print("  合并它即可发版并生成 CHANGELOG。")
        else:
            print(
                "  流水线已就位。下次带 feat:/fix: 的提交合入默认分支就会自动开 Release PR。"
            )

    except (pipeline.PipelineHalt, github.GitHubError, git.GitError) as exc:
        print(f"\n已停止: {exc}", file=sys.stderr)
        raise SystemExit(1)


def cmd_status(args: argparse.Namespace) -> None:
    repo_root = _resolve_repo()

    checks = {
        f".github/workflows/{WORKFLOW_FILENAME}": "GitHub Actions workflow",
        "release-please-config.json": "Release Please 配置",
        ".release-please-manifest.json": "版本清单",
        "CHANGELOG.md": "变更日志",
    }

    print(f"仓库: {repo_root.name}\n")
    for filepath, desc in checks.items():
        exists = (repo_root / filepath).exists()
        print(f"  [{'已存在' if exists else '缺失'}] {desc} ({filepath})")

    try:
        version = git.get_current_version(repo_root)
        print(f"\n  当前版本: {version or '无 tag'}")
    except git.GitError as exc:
        print(f"\n  当前版本: 读取失败 — {exc}")

    # 远端权限是整条流水线最容易出错的一环 —— 本地文件齐全也可能因为它而
    # 完全不工作。所以 status 必须把它显示出来。
    print()
    try:
        github.preflight()
        info = github.repo_info(repo_root)
        perms = github.get_workflow_permissions(info["nameWithOwner"])
        write_ok = perms.get("default_workflow_permissions") == "write"
        approve_ok = bool(perms.get("can_approve_pull_request_reviews"))
        print(f"  远端: {info['nameWithOwner']}（你的权限 {info.get('viewerPermission')}）")
        print(
            f"  [{'OK' if write_ok else '不足'}] workflow 写权限: "
            f"{perms.get('default_workflow_permissions')}"
        )
        print(f"  [{'OK' if approve_ok else '不足'}] 允许 Actions 创建 PR: {approve_ok}")
        if not (write_ok and approve_ok):
            print("\n  release-please 在当前权限下无法创建 Release PR。")
            print("  修复: deckhand setup --auto（或 Settings → Actions → General 手动开）")
    except (github.GitHubError, git.GitError) as exc:
        print(f"  远端状态: 无法查询 — {exc}")


def cmd_ship(args: argparse.Namespace) -> None:
    """手动触发一次发版评估并等待结果。"""
    repo_root = _resolve_repo()
    try:
        github.preflight()
        base = args.base or git.default_branch(repo_root)
        print(f"触发 {WORKFLOW_FILENAME} (ref={base})")
        github.dispatch_workflow(repo_root, WORKFLOW_FILENAME, ref=base)

        run = github.latest_run(repo_root, WORKFLOW_FILENAME)
        if not run:
            print("查不到 workflow run。确认已经跑过 deckhand setup。", file=sys.stderr)
            raise SystemExit(1)

        ok = github.watch_run(repo_root, run["databaseId"])
        url = run.get("url") or github.run_url(repo_root, run["databaseId"])
        if not ok:
            print(f"\nworkflow 失败: {url}", file=sys.stderr)
            raise SystemExit(1)
        print(f"\nworkflow 成功: {url}")

        release_pr = github.find_release_pr(repo_root)
        if release_pr:
            print(f"Release PR: {release_pr['url']}")
            print("合并它即可发版。")
        else:
            print("没有可发的内容 —— 上次 tag 之后没有 feat:/fix: 提交。")
    except (github.GitHubError, git.GitError) as exc:
        print(f"\n失败: {exc}", file=sys.stderr)
        raise SystemExit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="deckhand",
        description="DeckHand - CI 自动化的甲板水手",
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    setup_parser = subparsers.add_parser("setup", help="初始化发版配置")
    setup_parser.add_argument(
        "--backend",
        default="release-please",
        choices=list_backends(),
        help="发版后端 (默认: release-please)",
    )
    setup_parser.add_argument("--package-name", help="包名（默认: 远端仓库名）")
    setup_parser.add_argument("--changelog-path", help="CHANGELOG 文件路径")
    setup_parser.add_argument(
        "--release-type",
        choices=RELEASE_TYPES,
        help="release-please 的 release-type（默认按项目文件自动探测）",
    )
    setup_parser.add_argument("--base", help="默认分支名（默认自动探测）")
    setup_parser.add_argument(
        "--auto",
        action="store_true",
        help="全自动：推分支、开 Actions 权限、合并、触发、验证",
    )
    setup_parser.add_argument(
        "--allow-changelog-takeover",
        action="store_true",
        help="确认让 release-please 接管已存在的手写 CHANGELOG（默认会停下来问）",
    )
    setup_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="配合 --auto：只打印会执行的动作，不执行",
    )

    subparsers.add_parser("status", help="检查本地配置和远端权限状态")

    ship_parser = subparsers.add_parser("ship", help="触发一次发版并等待结果")
    ship_parser.add_argument("--base", help="触发所用的 ref（默认自动探测）")

    args = parser.parse_args()

    if args.command == "setup":
        cmd_setup(args)
    elif args.command == "status":
        cmd_status(args)
    elif args.command == "ship":
        cmd_ship(args)
    else:
        parser.print_help()
        raise SystemExit(1)


if __name__ == "__main__":
    main()
