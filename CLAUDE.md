# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OG Content Creator — a CLI tool that scans OpenGradient's GitHub repos for recent merged PRs and releases, then uses the Claude Agent SDK with the GitHub MCP server to synthesize activity into X (Twitter) post summaries.

## Commands

```bash
# Run (uses uv for dependency management)
uv run python main.py                        # default: weekly lookback (14 days)
uv run python main.py --frequency daily      # 1-day lookback
uv run python main.py --lookback-days 5      # custom lookback
uv run python main.py --output posts.txt     # write to file instead of stdout

# Dependencies
uv sync                                      # install/update deps from uv.lock
```

Requires a `.env` file with `GITHUB_TOKEN` and `ANTHROPIC_API_KEY`. The GitHub MCP server runs via Docker, so Docker must be running.

## Architecture

Three files, ~230 lines total:

- **main.py** — CLI entry point. Parses args, validates env vars, calls `draft_content_sync()`, handles output.
- **content_drafter.py** — Core logic. Builds system/user prompts, configures the GitHub MCP server (Docker-based), calls `claude_agent_sdk.query()` to stream agent responses. The agent uses MCP tools (`mcp__github__*`) to scan repos for PRs and releases.
- **config.py** — Static data: `PRODUCTS` maps product names to GitHub repos (grouped so multiple repos roll up into one product update), `LOOKBACK_DAYS` maps frequency strings to day counts.

The agent SDK handles all GitHub API interaction through the MCP server — there is no direct GitHub API code in this repo.
