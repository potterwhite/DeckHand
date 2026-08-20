"""GitHub 操作封装（基于 `gh` CLI）。

这个模块是「全自动」的关键。原本 skill 里让用户去浏览器点的四步 ——
开 Actions 权限、合并配置分支、触发首次发版、验证结果 —— 全部在这里
用 gh 做掉。

为什么用 `gh` 而不是直接调 REST API：认证已经由 gh 管好了（keyring /
GH_TOKEN / gh auth login 都能用），而且 owner/repo 的解析交给 gh 处理，
对各种奇怪的 remote 格式（SSH host alias、带不带 .git）都免疫。
"""

import json
import shutil
import subprocess
from pathlib import Path


class GitHubError(RuntimeError):
    """gh 命令执行失败。"""


def _gh(args: list[str], cwd: Path | None = None, check: bool = True) -> str:
    result = subprocess.run(
        ["gh", *args], capture_output=True, text=True, cwd=cwd
    )
    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "(无输出)"
        raise GitHubError(f"gh {' '.join(args)} 失败 (exit {result.returncode}):\n{detail}")
    return result.stdout.strip()


def _gh_json(args: list[str], cwd: Path | None = None) -> dict:
    out = _gh(args, cwd=cwd)
    try:
        return json.loads(out)
    except json.JSONDecodeError as exc:
        raise GitHubError(f"gh 返回的不是合法 JSON: {out[:200]}") from exc


# --------------------------------------------------------------------------
# 预检
# --------------------------------------------------------------------------

def preflight() -> None:
    """确认 gh 存在且已登录。

    提前检查，免得流水线跑到第四步改权限时才炸 —— 那时配置分支已经
    推上去了，状态更难收拾。
    """
    if shutil.which("gh") is None:
        raise GitHubError(
            "找不到 gh CLI。--auto 需要它来配置仓库权限和管理 PR。\n"
            "安装：https://cli.github.com/  然后 gh auth login"
        )
    result = subprocess.run(
        ["gh", "auth", "status"], capture_output=True, text=True
    )
    if result.returncode != 0:
        raise GitHubError(
            "gh 未登录。请先运行：gh auth login\n"
            + (result.stderr.strip() or result.stdout.strip())
        )


# --------------------------------------------------------------------------
# 仓库信息
# --------------------------------------------------------------------------

def repo_info(cwd: Path) -> dict:
    """返回 nameWithOwner / name / owner / viewerPermission / isPrivate。"""
    return _gh_json(
        [
            "repo",
            "view",
            "--json",
            "nameWithOwner,name,owner,viewerPermission,isPrivate,defaultBranchRef",
        ],
        cwd=cwd,
    )


def repo_slug(cwd: Path) -> str:
    """返回 owner/repo。"""
    return repo_info(cwd)["nameWithOwner"]


def can_administer(info: dict) -> bool:
    """当前用户是否有权改仓库设置。

    改 Actions workflow 权限需要 admin。MAINTAIN 拿不到这个 endpoint，
    所以要提前判断而不是等 403。
    """
    return info.get("viewerPermission") in ("ADMIN",)


# --------------------------------------------------------------------------
# Actions 权限 —— 原 skill 第四步「必须停下来」的那一步
# --------------------------------------------------------------------------

def get_workflow_permissions(slug: str) -> dict:
    """读当前的 workflow 权限设置。"""
    return _gh_json(["api", f"repos/{slug}/actions/permissions/workflow"])


def set_workflow_permissions(
    slug: str, *, write: bool = True, can_approve_prs: bool = True
) -> None:
    """开启 release-please 需要的两项权限。

    没有这两项，release-please 无法创建 Release PR —— 这是整条流水线
    最常见的失败原因，也是原 skill 唯一坚持要人工介入的地方。
    """
    _gh(
        [
            "api",
            "--method",
            "PUT",
            f"repos/{slug}/actions/permissions/workflow",
            "-F",
            f"default_workflow_permissions={'write' if write else 'read'}",
            "-F",
            f"can_approve_pull_request_reviews={str(can_approve_prs).lower()}",
        ]
    )


# --------------------------------------------------------------------------
# PR
# --------------------------------------------------------------------------

def create_pr(cwd: Path, *, base: str, head: str, title: str, body: str) -> str:
    """创建 PR，返回 URL。"""
    return _gh(
        [
            "pr", "create",
            "--base", base,
            "--head", head,
            "--title", title,
            "--body", body,
        ],
        cwd=cwd,
    )


def merge_pr(cwd: Path, ref: str, *, squash: bool = True, delete_branch: bool = True) -> None:
    """合并 PR。ref 可以是 PR 号、URL 或分支名。"""
    args = ["pr", "merge", ref, "--squash" if squash else "--merge"]
    if delete_branch:
        args.append("--delete-branch")
    _gh(args, cwd=cwd)


def find_release_pr(cwd: Path) -> dict | None:
    """查找 release-please 开的 Release PR。

    它会给自己的 PR 打 `autorelease: pending` label，这是最可靠的识别方式。
    """
    prs = _gh_json_list(
        ["pr", "list", "--label", "autorelease: pending", "--json", "number,title,url"],
        cwd=cwd,
    )
    return prs[0] if prs else None


def _gh_json_list(args: list[str], cwd: Path | None = None) -> list:
    out = _gh(args, cwd=cwd)
    try:
        data = json.loads(out)
    except json.JSONDecodeError as exc:
        raise GitHubError(f"gh 返回的不是合法 JSON: {out[:200]}") from exc
    return data if isinstance(data, list) else []


# --------------------------------------------------------------------------
# Workflow 触发与验证 —— 原第六、七步
# --------------------------------------------------------------------------

def dispatch_workflow(cwd: Path, workflow: str, *, ref: str) -> None:
    """手动触发 workflow。

    这是为什么生成的 workflow 里要带 workflow_dispatch —— 原 skill 用
    「造一个空文件 + 假的 feat: commit」来触发首次发版，会在仓库里留下
    垃圾文件和一个毫无意义的 release。dispatch 才是正路。
    """
    _gh(["workflow", "run", workflow, "--ref", ref], cwd=cwd)


def latest_run(cwd: Path, workflow: str) -> dict | None:
    """取该 workflow 最近一次运行。"""
    runs = _gh_json_list(
        [
            "run", "list",
            "--workflow", workflow,
            "--limit", "1",
            "--json", "databaseId,status,conclusion,url",
        ],
        cwd=cwd,
    )
    return runs[0] if runs else None


def watch_run(cwd: Path, run_id: int) -> bool:
    """阻塞等待某次运行结束。成功返回 True。

    --exit-status 让 gh 在 workflow 失败时返回非零，所以这里用
    check=False 自己判断，而不是让它抛错。
    """
    result = subprocess.run(
        ["gh", "run", "watch", str(run_id), "--exit-status"],
        cwd=cwd,
        text=True,
    )
    return result.returncode == 0


def run_url(cwd: Path, run_id: int) -> str:
    info = _gh_json(["run", "view", str(run_id), "--json", "url"], cwd=cwd)
    return info.get("url", "")
