"""Configuration for the pi (earendil-works/pi) CLI deployer."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class PiCliConfig:
    """Per-episode pi CLI settings."""

    name: ClassVar[str] = "pi_cli"

    model: str = "anthropic/claude-sonnet-4.6"
    """Model id. For ``provider="direct"`` this must be ``<vendor>/<id>``
    (e.g. ``anthropic/claude-sonnet-4.6``) — the vendor prefix is stripped and
    used to pick both the pi ``--provider`` flag and the API-key env var. For
    ``"openrouter"``/``"custom"`` it is passed through as-is."""

    provider: str = "openrouter"
    """Routing mode:
      - ``"openrouter"`` -> ``--provider openrouter --model <model>``, key
        from ``api_key`` or ``OPENROUTER_API_KEY``.
      - ``"direct"`` -> ``<vendor>/<id>`` split into ``--provider <vendor>
        --model <id>``, key from ``api_key`` or the vendor's own env var
        (``ANTHROPIC_API_KEY``/``OPENAI_API_KEY``/``GEMINI_API_KEY``/
        ``XAI_API_KEY``/``HF_TOKEN``).
      - ``"custom"`` -> ``--provider custom --model <model>``, requires
        ``base_url``; writes a ``models.json`` entry pi reads its request
        shape from (see ``max_tokens``), key from ``api_key`` or
        ``OPENROUTER_API_KEY``/``HF_TOKEN``."""

    base_url: str | None = None
    """OpenAI-compatible endpoint. Required (and only used) when
    ``provider="custom"``."""

    api_key: str | None = None
    """Literal API key, used in place of the provider's env-var key for any
    ``provider`` mode. ``None`` falls back to the env var documented under
    ``provider``."""

    cli_version: str = "0.85.1"
    """Version of ``@earendil-works/pi-coding-agent`` to install via npm."""

    thinking_level: str | None = None
    """Passed as ``--thinking <level>`` when set; provider-specific accepted
    values are validated by pi itself."""

    max_tokens: int = 65536
    """Max output tokens advertised to pi for provider="custom" (written into
    the models.json entry pi builds its request from). pi's own models.json
    schema defaults this to 16384 when omitted -- far too small for
    reasoning-heavy models (confirmed: GLM-5.3 hit stopReason="length" at
    exactly 16384 output tokens mid-calculation on every 0-scoring task in a
    real run, cut off before it could act on its own correct arithmetic).
    Only applies to provider="custom" -- openrouter/direct modes use pi's
    own built-in model catalog, which already carries correct per-model
    maxTokens values pi's maintainers keep updated."""

    disabled_tools: list[str] = field(default_factory=list)
    """Tool names passed as ``--exclude-tools a,b,c``."""

    extra_args: list[str] = field(default_factory=list)
    """Free-form flags appended verbatim to the pi CLI invocation."""
