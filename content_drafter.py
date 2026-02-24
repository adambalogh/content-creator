"""Use the Claude Agent SDK to draft holistic X posts from aggregated GitHub changes."""

from __future__ import annotations

import asyncio

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query


SYSTEM_PROMPT = """\
You are the content analyst for OpenGradient — a company building decentralized
AI infrastructure.  Your job is to translate recent GitHub activity into
high-level product updates that a human content writer will use to draft X
(Twitter) posts.

RULES:
1. You will receive raw GitHub activity (PRs, releases) grouped by product.
2. Produce ONE holistic summary per product — do NOT list individual PRs or
   describe code-level details like "added function X" or "refactored module Y".
3. Write from the perspective of a USER or the COMMUNITY — what can they now DO
   that they couldn't before?  What got faster, easier, or more reliable?
   Think product announcements, not changelogs.
4. Keep it non-technical.  A crypto/AI-curious person should understand every word.
   No function names, no file paths, no implementation details.
5. If a release is included, mention the version number.
6. Output using this format:

   === <Product Name> ===
   What's new: <1-3 sentences a general audience would understand>
   Suggested angle: <brief note on what would make this interesting to post about>

7. If there are no meaningful user-facing changes worth posting about, say so.
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
