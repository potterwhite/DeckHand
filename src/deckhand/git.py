"""DeckHand git 工具函数。"""

import subprocess
from pathlib import Path


def run(cmd: list[str], cwd: Path | None = None) -> str:
    """执行命令，返回 stdout。"""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.stdout.strip()


def is_git_repo(path: Path) -> bool:
    """检查路径是否是 git 仓库。"""
    return (path / ".git").exists()


def get_current_version(repo_root: Path) -> str | None:
    """从最新 tag 获取当前版本号。没有 tag 返回 None。"""
    output = run(["git", "describe", "--tags", "--abbrev=0"], cwd=repo_root)
    if not output:
        return None
    # 去掉开头的 'v'（如果有的话）
    return output.lstrip("v")


def get_repo_name(repo_root: Path) -> str:
    """获取仓库名。"""
    output = run(["git", "remote", "get-url", "origin"], cwd=repo_root)
    if output:
        return output.rsplit("/", 1)[-1].replace(".git", "")
    return repo_root.name
