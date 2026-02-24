"""OG Content Creator — propose X posts from OpenGradient's latest GitHub activity."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from config import LOOKBACK_DAYS
from content_drafter import draft_content_sync


def main() -> None:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Propose X posts from OpenGradient's latest GitHub activity.",
    )
    parser.add_argument(
        "--frequency",
        choices=["daily", "weekly"],
        default="weekly",
        help="How far back to look for changes (default: weekly).",
    )
    parser.add_argument(
        "--lookback-days",
        type=int,
        default=None,
        help="Override lookback window in days.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write proposed content to this file instead of stdout.",
    )

    args = parser.parse_args()

    if not os.getenv("GITHUB_TOKEN"):
        print("Error: GITHUB_TOKEN is required. Set it in .env.", file=sys.stderr)
        sys.exit(1)

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY is required. Set it in .env.", file=sys.stderr)
        sys.exit(1)

    lookback = args.lookback_days or LOOKBACK_DAYS.get(args.frequency, 14)

    print(f"Scanning GitHub and drafting content (lookback: {lookback} days)...", file=sys.stderr)
    content = draft_content_sync(lookback)

    output_file = Path(args.output) if args.output else None
    if output_file:
        output_file.write_text(content)
        print(f"Content written to {output_file}", file=sys.stderr)
    else:
        print("\n" + "=" * 60)
        print("PROPOSED X POSTS")
        print("=" * 60 + "\n")
        print(content)


if __name__ == "__main__":
    main()
