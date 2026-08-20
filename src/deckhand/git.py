"""DeckHand git 工具函数。

设计原则：git 命令失败必须抛错，绝不静默返回空值。
早期版本把 returncode 和 stderr 都丢掉了，结果 git 一出问题就静默
退回版本号 0.0.0 —— release-please 会据此从头开始编号，把一个
已经发到 v1.1.3 的仓库重置回 0.x。这类错误必须响。
"""

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    """git 命令执行失败。"""


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> str:
    """执行命令并返回 stdout。

    check=True（默认）时非零退出码抛 GitError，错误信息带上 stderr。
    只有在「失败是预期结果之一」的地方才传 check=False。
    """
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "(无输出)"
        raise GitError(f"命令失败 (exit {result.returncode}): {' '.join(cmd)}\n{detail}")
    return result.stdout.strip()


def find_repo_root(start: Path | None = None) -> Path | None:
    """向上查找 git 仓库根目录。不在仓库内返回 None。

    用 rev-parse 而不是检查 `.git` 是否存在 —— 后者只在仓库根目录下
    才为真，从子目录运行就会误判成「不是 git 仓库」。
    """
    start = start or Path.cwd()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        cwd=start,
    )
    if result.returncode != 0:
        return None
    top = result.stdout.strip()
    return Path(top) if top else None


def is_git_repo(path: Path) -> bool:
    """path 是否位于某个 git 仓库内（含子目录）。"""
    return find_repo_root(path) is not None


def get_current_version(repo_root: Path) -> str | None:
    """从 tag 推断当前版本号。仓库确实没有任何 tag 时返回 None。

    区分两种情况，这是关键：
      - 没有 tag        → None，调用方使用 0.0.0，这是合法的首次发版
      - git 执行出错     → 抛 GitError，绝不退回 0.0.0
    """
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    if result.returncode == 0:
        return result.stdout.strip().lstrip("v") or None

    stderr = result.stderr.lower()
    no_tags = "no names found" in stderr or "no tags can describe" in stderr
    if not no_tags:
        raise GitError(
            f"git describe 失败 (exit {result.returncode}): "
            f"{result.stderr.strip() or '(无输出)'}"
        )

    # describe 找不到「HEAD 的祖先里最近的 tag」。可能是真没 tag，
    # 也可能是 tag 存在但不在 HEAD 的历史上（例如刚开的孤立分支）。
    tags = run(["git", "tag", "--list", "--sort=-v:refname"], cwd=repo_root)
    if not tags:
        return None
    return tags.splitlines()[0].strip().lstrip("v") or None


def get_repo_name(repo_root: Path) -> str:
    """从 origin remote 推断仓库名，拿不到就退回目录名。

    注意：这个函数只是兜底。需要 owner/repo 时一律走
    github.repo_slug()，它用 `gh` 解析，对 SSH host alias
    这类 remote（形如 `MyAlias:owner/repo.git`）也正确 —— 用字符串
    切分那种 remote 会把 owner 丢掉。
    """
    url = run(["git", "remote", "get-url", "origin"], cwd=repo_root, check=False)
    if url:
        name = url.rstrip("/").rsplit("/", 1)[-1]
        if name.endswith(".git"):
            name = name[:-4]
        if name:
            return name
    return repo_root.name


def is_clean(repo_root: Path) -> bool:
    """工作区是否干净（无已修改/未跟踪文件）。"""
    return not run(["git", "status", "--porcelain"], cwd=repo_root)


def dirty_files(repo_root: Path) -> list[str]:
    """列出未提交的改动，用于报错时说明拦下了什么。"""
    out = run(["git", "status", "--porcelain"], cwd=repo_root)
    return [line.strip() for line in out.splitlines() if line.strip()]


def current_branch(repo_root: Path) -> str:
    return run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)


def default_branch(repo_root: Path) -> str:
    """推断远端默认分支，拿不到就退回 main。"""
    ref = run(
        ["git", "symbolic-ref", "refs/remotes/origin/HEAD"],
        cwd=repo_root,
        check=False,
    )
    if ref:
        return ref.rsplit("/", 1)[-1]
    return "main"


def branch_exists(repo_root: Path, name: str) -> bool:
    result = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", f"refs/heads/{name}"],
        capture_output=True,
        text=True,
        cwd=repo_root,
    )
    return result.returncode == 0
