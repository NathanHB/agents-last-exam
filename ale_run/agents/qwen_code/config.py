"""QwenCodeConfig: per-episode knobs for the Qwen Code CLI deployer.

Qwen Code (https://github.com/QwenLM/qwen-code) is QwenLM's own coding-agent
CLI -- an actively-developed fork/parity-target of Claude Code, published on
npm as ``@qwen-code/qwen-code``. Auth/model routing is entirely env-var
driven, no LiteLLM layer and no config file to write: setting
``OPENAI_API_KEY`` + ``OPENAI_MODEL`` + ``OPENAI_BASE_URL`` together is
enough for the CLI to auto-infer ``AuthType.USE_OPENAI``
(``getAuthTypeFromEnv`` in ``packages/cli/src/utils/modelConfigUtils.ts``) --
no ``qwen auth`` step, no on-disk provider registry (unlike zcode).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class QwenCodeConfig:
    """Tunables for :class:`QwenCodeDeployer`.

    Standalone config (no shared base). The episode wall-budget is
    orchestration-owned; ``timeout_s`` is no longer an agent knob.
    """

    name: ClassVar[str] = "qwen_code"

    model: str = "Qwen/Qwen3.5-9B"
    """Model id, sent as-is via ``OPENAI_MODEL`` -- no LiteLLM prefix
    convention here, this is a real OpenAI-compatible-chat-completions
    request, not a routed one."""

    base_url: str = "https://router.huggingface.co/v1"
    """OpenAI-compatible base URL (``OPENAI_BASE_URL``)."""

    api_key: str | None = None
    """Literal API key (``OPENAI_API_KEY``). Required -- there is no
    provider-name heuristic or env-var fallback name to guess here (unlike
    openhands_cli's provider-driven OPENROUTER_API_KEY/ANTHROPIC_API_KEY
    convention); set ``api_key: ${env:HF_TOKEN}`` in the agent yaml."""

    cli_version: str = "0.24.4"
    """Version of the ``@qwen-code/qwen-code`` npm package to install.
    Pinned (not ``latest``) for reproducibility -- confirmed working via a
    real local run and a real HF Jobs sandbox smoke test at this version."""

    extra_envs: dict[str, str] = field(default_factory=dict)
    """Free-form passthrough env vars exported to the qwen subprocess.
    Keys here override anything the deployer would otherwise compute."""
