"""全自动发版配置流水线。

把原本需要用户在浏览器里点的四步做完：
  4. 开 Actions workflow 权限   → gh api PUT .../actions/permissions/workflow
  5. 合并配置分支               → gh pr create + gh pr merge --squash
  6. 触发首次发版               → gh workflow run（靠 workflow_dispatch）
  7. 验证                       → gh run watch + 查 autorelease: pending

护栏的设计前提：这个流程会改仓库设置并往默认分支推东西。所有不可逆的
动作之前都要么有检查、要么能还原、要么停下来问。
"""

from dataclasses import dataclass, field
from pathlib import Path

from deckhand import git, github
from deckhand.backends.release_please import WORKFLOW_FILENAME
from deckhand.config import DeckHandConfig, changelog_looks_managed

CONFIG_BRANCH = "chore/init-ci"


class PipelineHalt(RuntimeError):
    """流水线主动停下，需要人来决定。不是 bug，是设计。"""


@dataclass
class Plan:
    """要执行的动作清单。dry-run 就是把它打印出来而不执行。"""

    steps: list[str] = field(default_factory=list)

    def add(self, description: str) -> None:
        self.steps.append(description)

    def render(self) -> str:
        lines = ["将要执行的动作：", ""]
        for i, step in enumerate(self.steps, 1):
            lines.append(f"  {i}. {step}")
        return "\n".join(lines)


# --------------------------------------------------------------------------
# 护栏
# --------------------------------------------------------------------------

def check_preconditions(
    repo_root: Path,
    config: DeckHandConfig,
    *,
    allow_changelog_takeover: bool = False,
) -> dict:
    """跑 --auto 之前的全部前置检查。任何一条不过就抛 PipelineHalt。

    返回 gh 的 repo_info，后面几步要用，避免重复请求。
    """
    github.preflight()

    # 工作区必须干净 —— 否则 `git add .` 会把用户没提交的改动一起卷进
    # 配置 commit 里推上去。
    if not git.is_clean(repo_root):
        files = git.dirty_files(repo_root)
        listing = "\n".join(f"    {f}" for f in files[:20])
        more = f"\n    ...另有 {len(files) - 20} 项" if len(files) > 20 else ""
        raise PipelineHalt(
            f"工作区有未提交的改动，拒绝执行 --auto：\n{listing}{more}\n\n"
            "先提交或 stash，再重跑。"
        )

    info = github.repo_info(repo_root)

    # 改 Actions 权限需要 admin。提前判断，而不是等第四步吃 403 —— 那时
    # 配置分支已经推上去了。
    if not github.can_administer(info):
        raise PipelineHalt(
            f"你对 {info['nameWithOwner']} 的权限是 "
            f"{info.get('viewerPermission')}，不是 ADMIN。\n"
            "修改 Actions workflow 权限需要 admin，这一步无法自动完成。\n"
            "请让仓库管理员在 Settings → Actions → General 里设置："
            "\n  - Workflow permissions: Read and write"
            "\n  - 勾选 Allow GitHub Actions to create and approve pull requests"
        )

    # 已存在的手写 CHANGELOG 是真的会被 release-please 接管并改格式的。
    # 这个必须停下来问，不能替用户决定。
    changelog = repo_root / config.changelog_path
    if (
        not allow_changelog_takeover
        and changelog.exists()
        and not changelog_looks_managed(changelog)
    ):
        size = changelog.stat().st_size
        raise PipelineHalt(
            f"{config.changelog_path} 已存在（{size} 字节）且不像 "
            "release-please 生成的格式。\n"
            "release-please 会接管这个文件并按自己的格式写入，手写内容会被混进去。\n\n"
            "先选一个：\n"
            f"  - 备份改名：mv {config.changelog_path} CHANGELOG.old.md\n"
            f"  - 或指定别的路径：--changelog-path docs/CHANGELOG.md\n"
            f"  - 或确认要让它接管：--allow-changelog-takeover"
        )

    return info


# --------------------------------------------------------------------------
# 流水线
# --------------------------------------------------------------------------

def build_plan(config: DeckHandConfig, slug: str, files: list[str]) -> Plan:
    plan = Plan()
    plan.add(f"在 {CONFIG_BRANCH} 分支写入 {len(files)} 个文件: {', '.join(files)}")
    plan.add(f"git checkout -b {CONFIG_BRANCH}")
    plan.add("git add <上述文件> && git commit -m 'chore: bootstrap release-please …'")
    plan.add(f"git push --set-upstream origin {CONFIG_BRANCH}")
    plan.add(
        f"gh api --method PUT repos/{slug}/actions/permissions/workflow "
        "-F default_workflow_permissions=write "
        "-F can_approve_pull_request_reviews=true"
    )
    plan.add(f"gh pr create --base {config.default_branch} --head {CONFIG_BRANCH} …")
    plan.add("gh pr merge --squash --delete-branch")
    plan.add(f"gh workflow run {WORKFLOW_FILENAME} --ref {config.default_branch}")
    plan.add("gh run watch <id> --exit-status")
    plan.add("查询 autorelease: pending 标签，报告 Release PR")
    return plan


def run_auto(
    repo_root: Path,
    config: DeckHandConfig,
    files: dict[str, str],
    *,
    info: dict,
    echo=print,
) -> dict:
    """执行完整流水线。返回结果摘要。"""
    slug = info["nameWithOwner"]
    base = config.default_branch
    result: dict = {"slug": slug, "base": base}

    # --- 1. 建分支 ---
    if git.branch_exists(repo_root, CONFIG_BRANCH):
        raise PipelineHalt(
            f"分支 {CONFIG_BRANCH} 已存在。先删掉或改名：\n"
            f"  git branch -D {CONFIG_BRANCH}"
        )
    echo(f"[1/7] 创建分支 {CONFIG_BRANCH}")
    git.run(["git", "checkout", "-b", CONFIG_BRANCH], cwd=repo_root)

    # --- 2. 写文件 ---
    echo(f"[2/7] 写入 {len(files)} 个配置文件")
    written = []
    for filepath, content in files.items():
        target = repo_root / filepath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        written.append(filepath)
        echo(f"       {filepath}")

    # --- 3. 提交并推送 ---
    echo("[3/7] 提交并推送")
    git.run(["git", "add", *written], cwd=repo_root)
    message = (
        "chore: bootstrap release-please configuration\n\n"
        f"release-type: {config.release_type}\n"
        f"starting version: {config.current_version}\n"
    )
    git.run(["git", "commit", "-m", message], cwd=repo_root)
    git.run(
        ["git", "push", "--set-upstream", "origin", CONFIG_BRANCH], cwd=repo_root
    )

    # --- 4. 开权限（原来要人去点浏览器的那一步）---
    echo("[4/7] 配置 Actions workflow 权限")
    before = github.get_workflow_permissions(slug)
    result["permissions_before"] = before
    echo(f"       原值: {before}")
    if before.get("default_workflow_permissions") == "write" and before.get(
        "can_approve_pull_request_reviews"
    ):
        echo("       已满足要求，跳过")
    else:
        github.set_workflow_permissions(slug, write=True, can_approve_prs=True)
        after = github.get_workflow_permissions(slug)
        result["permissions_after"] = after
        echo(f"       新值: {after}")
        echo(
            "       如需还原: gh api --method PUT "
            f"repos/{slug}/actions/permissions/workflow "
            f"-F default_workflow_permissions={before.get('default_workflow_permissions', 'read')} "
            f"-F can_approve_pull_request_reviews={str(before.get('can_approve_pull_request_reviews', False)).lower()}"
        )

    # --- 5. 建 PR 并合并 ---
    echo("[5/7] 创建并合并配置 PR")
    pr_url = github.create_pr(
        repo_root,
        base=base,
        head=CONFIG_BRANCH,
        title="chore: bootstrap release-please configuration",
        body=(
            "由 DeckHand 自动生成。\n\n"
            f"- release-type: `{config.release_type}`\n"
            f"- 起始版本: `{config.current_version}`\n"
            f"- 监听分支: `{base}`\n\n"
            "标题用 `chore:` 前缀，所以这个 PR 本身不会触发发版。"
        ),
    )
    result["config_pr"] = pr_url
    echo(f"       {pr_url}")
    github.merge_pr(repo_root, CONFIG_BRANCH, squash=True, delete_branch=True)
    echo("       已 squash 合并")

    # 回到默认分支并拉取合并后的状态
    git.run(["git", "checkout", base], cwd=repo_root)
    git.run(["git", "pull", "--ff-only"], cwd=repo_root, check=False)

    # --- 6. 触发 ---
    echo(f"[6/7] 触发 {WORKFLOW_FILENAME}")
    github.dispatch_workflow(repo_root, WORKFLOW_FILENAME, ref=base)

    # --- 7. 验证 ---
    echo("[7/7] 等待 workflow 结束")
    run = github.latest_run(repo_root, WORKFLOW_FILENAME)
    if not run:
        raise PipelineHalt(
            "触发后查不到 workflow run。到 Actions 页面确认 workflow 是否被识别。"
        )
    run_id = run["databaseId"]
    ok = github.watch_run(repo_root, run_id)
    result["run_url"] = run.get("url") or github.run_url(repo_root, run_id)
    result["run_ok"] = ok
    if not ok:
        raise PipelineHalt(
            f"workflow 运行失败: {result['run_url']}\n"
            "配置已经合并进默认分支，权限也已设置 —— 看日志修完再重跑 "
            "`deckhand ship` 即可，不用重新 setup。"
        )
    echo("       workflow 成功")

    release_pr = github.find_release_pr(repo_root)
    result["release_pr"] = release_pr
    if release_pr:
        echo(f"       Release PR: {release_pr['url']}")
    else:
        echo(
            "       没有 Release PR —— 说明上次 tag 之后没有 feat:/fix: 提交，"
            "没有可发的东西。这是正常状态，不是失败。"
        )

    return result
