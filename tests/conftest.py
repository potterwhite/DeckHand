"""共享 fixture。"""

import subprocess
from pathlib import Path

import pytest


def _git(args: list[str], cwd: Path) -> None:
    subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    """一个最小的真实 git 仓库，无 tag。"""
    _git(["init", "-b", "main"], tmp_path)
    _git(["config", "user.email", "t@example.com"], tmp_path)
    _git(["config", "user.name", "Test"], tmp_path)
    (tmp_path / "README.md").write_text("hi\n")
    _git(["add", "."], tmp_path)
    _git(["commit", "-m", "chore: init"], tmp_path)
    return tmp_path


@pytest.fixture
def tagged_repo(repo: Path) -> Path:
    """带 v1.1.3 tag 的仓库。"""
    _git(["tag", "v1.1.3"], repo)
    return repo
