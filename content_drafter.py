"""Use the Claude Agent SDK to draft holistic X posts from aggregated GitHub changes."""

from __future__ import annotations

import asyncio

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query


SYSTEM_PROMPT = """\
You are the content analyst for OpenGradient — a company building decentralized
AI infrastructure.  Your job is to summarize recent GitHub activity into clear,
concise change descriptions that a human content writer will use to draft X
(Twitter) posts.

RULES:
1. You will receive a summary of recent GitHub activity grouped by product.
2. Produce ONE holistic summary per product — do NOT list every PR separately.
   Synthesize related changes into a coherent description of what the product
   improved or shipped.
3. Focus on WHAT changed and WHY it matters — not on drafting tweet copy.
   A human will write the actual posts.
4. Use plain, technical-but-accessible language.  Be specific about capabilities
   and improvements.  Avoid marketing fluff.
5. If a release is included, mention the version.
6. Output using this format:

   === <Product Name> ===
   Summary: <1-3 sentence high-level description of what changed>
   Key changes:
   - <change 1>
   - <change 2>
   Suggested angle: <brief note on what would make this interesting to post about>

7. If there are no meaningful changes worth posting about, say so briefly.
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
