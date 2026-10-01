"""ZCodeConfig: per-episode knobs for the ZCode deployer.

ZCode (https://github.com/zai-org/ZCode) is Z.ai's own coding-agent CLI --
a TypeScript/Node monorepo, NOT a Claude Code fork. It has no LiteLLM layer
and no published npm package (``zcode-cli``/``@zcode/cli`` are not on the
npm registry as of 2026-09), so the deployer builds it from source every
install: clone, ``pnpm install --filter @zcode/cli...``, ``pnpm --filter
@zcode/cli build`` -> ``apps/zcode-cli/packages/cli/dist/zcode.cjs``.

Model/provider routing is entirely file-based (no ``--model`` CLI flag
exists): the deployer writes a "personal" provider-config JSON
(``ZCODE_PERSONAL_PROVIDER_CONFIG_FILE``) declaring one custom
``openai-chat-completions`` provider plus a paired minimal "builtin"
provider-config JSON (``ZCODE_BUILTIN_PROVIDER_CONFIG_FILE``, required to be
set whenever the personal one is, per ``prepareCliProviderRuntimeEnv`` --
both-or-neither). See ``deployer.py`` module docstring for the exact JSON
shapes (reverse-engineered from ``packages/provider/src/config/*.ts``'s zod
schemas).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class ZCodeConfig:
    """Tunables for :class:`ZCodeDeployer`.

    Standalone config (no shared base, no LiteLLM). ``model``/``base_url``/
    ``api_key`` describe a single OpenAI-chat-completions-compatible
    provider that the deployer registers with ZCode as a custom provider
    named ``provider_id`` -- there is no vendor-name heuristic, just this
    one endpoint.
    """

    name: ClassVar[str] = "zcode"

    model: str = "Qwen/Qwen3.5-9B"
    """Model id as the upstream OpenAI-compatible endpoint expects it
    (passed through verbatim in the provider config's ``personalModelIds``
    and ``defaultModelSelection.modelId`` -- no prefix rewriting)."""

    provider_id: str = "hf-router"
    """Arbitrary id for the custom provider entry ZCode registers this
    endpoint under (``defaultModelSelection.providerId`` and the
    provider-config's ``providerId``). Cosmetic; must just be unique and
    URL/id-safe."""

    base_url: str = "https://router.huggingface.co/v1"
    """OpenAI-chat-completions-compatible base URL
    (``provider.config.api.baseUrl``)."""

    api_key: str | None = None
    """Literal API key (``provider.config.access.apiKey``). Required --
    ZCode's custom-provider path has no natural env-var fallback name to
    default to (unlike the LiteLLM-routed agents in this repo), so a
    missing key is a hard error at install time. Set via ``api_key:
    ${env:HF_TOKEN}`` in the agent yaml."""

    cli_ref: str = "main"
    """Git ref (branch/tag/sha) of https://github.com/zai-org/ZCode to
    build. No tagged release has been vetted for this integration yet --
    pin to a specific sha once one has been, to stop the build silently
    drifting."""

    extra_envs: dict[str, str] = field(default_factory=dict)
    """Free-form passthrough env vars exported to the ``zcode`` subprocess
    (e.g. proxy settings). Keys here override anything the deployer would
    otherwise compute."""
