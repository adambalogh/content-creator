"""Use the Claude Agent SDK to draft holistic X posts from aggregated GitHub changes."""

from __future__ import annotations

import asyncio

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query


SYSTEM_PROMPT = """\
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
Translate recent GitHub activity into high-level product updates that a human
content writer will use to draft X (Twitter) posts.

RULES:
1. You will receive raw GitHub activity (PRs, releases) grouped by product.
2. Produce one or more holistic summary per product.  Synthesize all changes into a
   cohesive product update — what users can now do, what got better.
3. Write for a general crypto/AI-curious audience.  Keep it high-level.
4. If a release is included, mention the version number.
5. Output ONLY the summaries using this format — no additional notes, no
   commentary about what was left out, no writer instructions:

   === <Product Name> ===
   What's new: <1-3 sentences a general audience would understand>
   Why it matters: <one line on why a user/developer should care>
   Suggested angle: <what makes this interesting to post about>

6. If there are no meaningful user-facing changes, just say "No notable updates."
7. Do not highlight low-level technical changes or internal improvements or small bug fixes.
"""


async def draft_content(changes_text: str) -> str:
    """Send the aggregated changes to Claude and return the drafted posts.

    Args:
        changes_text: pre-formatted text block of product changes.

    Returns:
        The drafted X posts as a single string.
    """
    prompt = (
        "Here are the recent GitHub changes for OpenGradient, grouped by product.\n"
        "Summarize the notable changes per product so a human can draft X posts.\n\n"
        f"{changes_text}"
    )

    options = ClaudeAgentOptions(
        system_prompt=SYSTEM_PROMPT,
        max_turns=1,
    )

    result_parts: list[str] = []

    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    result_parts.append(block.text)
        elif isinstance(message, ResultMessage):
            if message.is_error:
                raise RuntimeError(f"Agent error after {message.num_turns} turns: {message.result}")

    return "\n".join(result_parts)


def draft_content_sync(changes_text: str) -> str:
    """Synchronous wrapper around draft_content for convenience."""
    return asyncio.run(draft_content(changes_text))
