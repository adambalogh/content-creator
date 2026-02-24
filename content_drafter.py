"""Use the Claude Agent SDK with the GitHub MCP server to scan repos and draft X posts."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta, timezone

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query

from config import PRODUCTS


def _build_system_prompt() -> str:
    return """\
You are the content analyst for OpenGradient.

ABOUT OPENGRADIENT:
OpenGradient is the network for open intelligence — a decentralized AI
infrastructure platform where developers can host, execute, and verify AI models
at scale with cryptographic proof of authenticity.  Key products include:
- x402 LLM Inference: payment-gated access to models (OpenAI, Anthropic, Google,
  etc.) verified through Trusted Execution Environments (TEEs), paid with OPG tokens. Powered by OpenGradient's verifiable inference infrastructure.
- Model Hub: a decentralized model repository (linear regression to LLMs to
  stable diffusion) built on Walrus storage.
- MemSync: a verifiable memory layer for AI apps — extracts, classifies, and
  stores user memories with full transparency. Secured by OpenGradient's verifiable inference infrastructure.
- Python SDK: toolkit for building apps with integrated LLM inference and model
  management using OpenGradient's blockchain infrastructure.

Every inference includes cryptographic attestation proving which models and
prompts were used, enabling transparent, auditable AI agent actions.

YOUR JOB:
1. Use the GitHub MCP tools to scan the specified repositories for recent merged
   pull requests and releases.
2. Synthesize the activity into high-level product updates that a human content
   writer will use to draft X (Twitter) posts.

SCANNING INSTRUCTIONS:
- For each repo, use the GitHub tools to list recently merged pull requests and
  releases within the lookback window.
- Group findings by product (multiple repos may belong to one product).
- Focus on user-facing changes — skip minor internal fixes.

OUTPUT RULES:
1. Produce one or more holistic summary per product.  Synthesize all changes into a
   cohesive product update — what users can now do, what got better.
2. Write for a general crypto/AI-curious audience.  Keep it high-level.
3. If a release is included, mention the version number.
4. Output ONLY the summaries using this format — no additional notes, no
   commentary about what was left out, no writer instructions:

   === <Product Name> ===
   What's new: <1-3 sentences a general audience would understand>
   Why it matters: <one line on why a user/developer should care>
   Suggested angle: <what makes this interesting to post about>

5. If there are no meaningful user-facing changes for a product, say "No notable updates."
6. Do not highlight low-level technical changes or internal improvements or small bug fixes.
"""


def _build_prompt(lookback_days: int) -> str:
    since = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    since_str = since.strftime("%Y-%m-%d")

    repo_list = "\n".join(
        f"  - Product: {product}\n    Repos: {', '.join(repos)}"
        for product, repos in PRODUCTS.items()
    )

    return (
        f"Scan the following GitHub repos for merged PRs and releases since {since_str} "
        f"(last {lookback_days} days). Then summarize the notable changes per product "
        f"so a human can draft X posts.\n\n"
        f"Products and repos:\n{repo_list}"
    )


async def draft_content(lookback_days: int) -> str:
    """Use the GitHub MCP server to scan repos and draft X post summaries.

    Args:
        lookback_days: how many days back to look for activity.

    Returns:
        The drafted X post summaries as a single string.
    """
    options = ClaudeAgentOptions(
        system_prompt=_build_system_prompt(),
        mcp_servers={
            "github": {
                "command": "docker",
                "args": [
                    "run", "-i", "--rm",
                    "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
                    "ghcr.io/github/github-mcp-server",
                ],
                "env": {
                    "GITHUB_PERSONAL_ACCESS_TOKEN": os.environ.get("GITHUB_TOKEN", ""),
                },
            },
        },
        allowed_tools=["mcp__github__*"],
    )

    prompt = _build_prompt(lookback_days)
    result_parts: list[str] = []

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result_parts.append(block.text)
        elif isinstance(message, ResultMessage):
            if message.is_error:
                raise RuntimeError(
                    f"Agent error after {message.num_turns} turns: {message.result}"
                )

    return "\n".join(result_parts)


def draft_content_sync(lookback_days: int) -> str:
    """Synchronous wrapper around draft_content."""
    return asyncio.run(draft_content(lookback_days))
