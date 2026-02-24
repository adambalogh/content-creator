"""OG Content Creator — propose X posts from OpenGradient's latest GitHub activity."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

from config import LOOKBACK_DAYS, PRODUCTS, ContentConfig
from content_drafter import draft_content_sync
from github_scanner import format_changes_for_prompt, scan_repos


def load_config(args: argparse.Namespace) -> ContentConfig:
    """Build a ContentConfig from CLI args + environment variables."""
    load_dotenv()

    import os

    github_token = args.github_token or os.getenv("GITHUB_TOKEN", "")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")

    if not github_token:
        print("Error: GITHUB_TOKEN is required. Set it in .env or pass --github-token.", file=sys.stderr)
        sys.exit(1)

    if not anthropic_key:
        print("Error: ANTHROPIC_API_KEY is required. Set it in .env.", file=sys.stderr)
        sys.exit(1)

    frequency = args.frequency
    lookback = args.lookback_days or LOOKBACK_DAYS.get(frequency, 7)

    return ContentConfig(
        frequency=frequency,
        lookback_days=lookback,
        github_token=github_token,
        anthropic_api_key=anthropic_key,
        output_file=Path(args.output) if args.output else None,
        products=PRODUCTS,
    )


def main() -> None:
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
        "--github-token",
        default=None,
        help="GitHub PAT. Falls back to GITHUB_TOKEN env var.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Write proposed content to this file instead of stdout.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only scan GitHub — skip content drafting.",
    )

    args = parser.parse_args()
    cfg = load_config(args)

    # 1. Scan GitHub
    print(f"Scanning GitHub repos (lookback: {cfg.lookback_days} days)...", file=sys.stderr)
    products = scan_repos(cfg.products, cfg.lookback_days, cfg.github_token)

    if not products:
        print("No notable changes found. Nothing to post.", file=sys.stderr)
        return

    changes_text = format_changes_for_prompt(products)

    if args.dry_run:
        print("\n--- Raw changes (dry-run) ---\n")
        print(changes_text)
        return

    # 2. Draft content with Claude
    print("Drafting content with Claude...", file=sys.stderr)
    content = draft_content_sync(changes_text)

    # 3. Output
    if cfg.output_file:
        cfg.output_file.write_text(content)
        print(f"Content written to {cfg.output_file}", file=sys.stderr)
    else:
        print("\n" + "=" * 60)
        print("PROPOSED X POSTS")
        print("=" * 60 + "\n")
        print(content)


if __name__ == "__main__":
    main()
