"""``task_data_source: mounted:<sandbox_dir>`` — task data already visible
*inside* the sandbox at ``<sandbox_dir>/<domain>/<task>/<variant>/`` (e.g. a
read-only HF bucket mounted into the sandbox job by the ``hfsandbox`` provider,
or any NFS/FUSE share the sandbox can see). Copies with plain ``cp`` via the
sandbox's cua-server, so it works on every provider — nothing runs on the host.

Layout expected under ``<sandbox_dir>`` is the one produced by extracting the
published ``ale-tasks-data.tar.gz``::

    <domain>/<task>/<variant>/{input,software,reference}

Phase 1 (``stage_input``): copy ``input/`` (+ ``software/``, made executable)
into the task dir and create ``output/``. Phase 3 (``stage_reference``): copy
``reference/`` — only after the agent has finished, so it never sees answers.
Linux-only (the mount point is a POSIX path).
"""
from __future__ import annotations

import logging
from typing import Any

from ...base_interface import SandboxHandle, TaskDataSpec
from . import join, shell_q, task_subdir

logger = logging.getLogger(__name__)

_PREFIX = "mounted:"


def _mounted_task_dir(source: str, task_data: TaskDataSpec) -> str:
    root = source[len(_PREFIX):].rstrip("/")
    if not root:
        raise ValueError("task_data_source=mounted: expected 'mounted:<sandbox_dir>'")
    return "/".join([
        root, task_data.domain_name or "", task_data.task_name or "",
        task_data.variant_name or "",
    ])


async def _copy_tree(sandbox: SandboxHandle, src: str, dst: str, *, timeout: float) -> None:
    """``cp -a src/. dst/`` — copies CONTENTS into dst whether or not it exists."""
    await sandbox.mkdir(dst)
    r = await sandbox.run_command(
        f"cp -a {shell_q(sandbox, src)}/. {shell_q(sandbox, dst)}/", timeout=timeout,
    )
    if r.returncode != 0:
        raise RuntimeError(
            f"task_data_source=mounted: cp {src} -> {dst} failed (rc={r.returncode}): "
            f"{(r.stderr or r.stdout or '')[:300]}"
        )


async def stage_input(
    sandbox: SandboxHandle, task_data: TaskDataSpec, *, source: str,
) -> dict[str, Any]:
    """Copy input/ (+ software/) from the mount into the task dir; make output/."""
    if not sandbox.is_linux:
        raise NotImplementedError("task_data_source=mounted is Linux-only")
    src = _mounted_task_dir(source, task_data)
    if not await sandbox.exists(f"{src}/input"):
        raise RuntimeError(
            f"task_data_source=mounted: expected input/ at {src!r} inside the sandbox, "
            f"not found. Is the task-data volume mounted at {source[len(_PREFIX):]!r}?"
        )
    base = task_subdir(sandbox, task_data)
    await _copy_tree(sandbox, f"{src}/input", join(sandbox, base, "input"), timeout=1800)
    await sandbox.mkdir(join(sandbox, base, "output"))
    staged = ["input"]
    if await sandbox.exists(f"{src}/software"):
        sw_dst = join(sandbox, base, "software")
        await _copy_tree(sandbox, f"{src}/software", sw_dst, timeout=1800)
        # mirror baked_in_sandbox / local: software wrappers must be executable.
        await sandbox.run_command(
            f"find {shell_q(sandbox, sw_dst)} -type f -exec chmod +x {{}} +", timeout=120,
        )
        staged.append("software")
    logger.info("mounted: staged %s for %s from %s", staged, task_data.task_name, src)
    return {"staged": staged, "source": "mounted"}


async def stage_reference(
    sandbox: SandboxHandle, task_data: TaskDataSpec, *, source: str,
) -> dict[str, Any]:
    """Copy reference/ — AFTER the agent, right before evaluate."""
    if not sandbox.is_linux:
        raise NotImplementedError("task_data_source=mounted is Linux-only")
    src = _mounted_task_dir(source, task_data)
    if not await sandbox.exists(f"{src}/reference"):
        return {"skipped": True, "reason": "no_reference"}
    base = task_subdir(sandbox, task_data)
    target = join(sandbox, base, "reference")
    await sandbox.rm([target])  # defend against stale reference from a prior run
    await _copy_tree(sandbox, f"{src}/reference", target, timeout=1800)
    logger.info("mounted: staged reference %s -> %s", src, target)
    return {"staged": ["reference"], "source": "mounted"}
