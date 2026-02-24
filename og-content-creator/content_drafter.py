"""Use the Claude Agent SDK to draft holistic X posts from aggregated GitHub changes."""

from __future__ import annotations

import asyncio

from claude_agent_sdk import AssistantMessage, ClaudeAgentOptions, ResultMessage, TextBlock, query

from config import MAX_THREAD_POSTS, MAX_TWEET_LENGTH

SYSTEM_PROMPT = f"""\
You are the social media content strategist for OpenGradient — a company building
decentralized AI infrastructure.  Your job is to draft engaging posts for the
company's X (Twitter) account.

RULES:
1. You will receive a summary of recent GitHub activity grouped by product.
2. Produce ONE holistic update per product — do NOT create a separate post for
   every PR.  Synthesize the changes into a coherent narrative about what the
   product improved or shipped.
3. Keep each individual post under {MAX_TWEET_LENGTH} characters.
4. If there is enough material, you may propose a short thread (max {MAX_THREAD_POSTS}
   posts) — but a single punchy tweet is preferred when possible.
5. Use a confident, technical-but-accessible tone.  Avoid generic hype.
   Highlight concrete capabilities or improvements.
6. Include relevant hashtags sparingly (1-2 max, e.g. #DecentralizedAI #OpenGradient).
7. If a release is included, mention the version.
8. Output ONLY the proposed posts — no extra commentary.  Use this format:

   === <Product Name> ===
   [Post 1]
   ---
   [Post 2]  (if thread)
   ---
   ...

9. If there are no meaningful changes worth posting about, say so briefly.
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
        "Draft holistic X posts for each product that has notable updates.\n\n"
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
