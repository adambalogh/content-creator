"""Configuration for the OG Content Creator agent."""

# ---------------------------------------------------------------------------
# GitHub repos to monitor.  Each entry maps a friendly *product name* to one
# or more GitHub "owner/repo" strings.  PRs from repos that share a product
# name are aggregated into a single holistic update.
# ---------------------------------------------------------------------------
PRODUCTS: dict[str, list[str]] = {
    "OpenGradient Blockchain": [
        "OpenGradient/og-evm",
    ],
    "OpenGradient SDK": [
        "OpenGradient/OpenGradient-SDK"
    ],
    "OpenGradient Verifiable Inference": [
        "OpenGradient/x402",
        "OpenGradient/tee-gateway",
        "OpenGradient/llm-server",
        "OpenGradient/inference-facilitator"
    ],
    "OpenGradient MemSync": [
        "OpenGradient/memsync",
        "OpenGradient/mem-chat-api",
    ],
    "BitQuant": [
        "OpenGradient/bitquant",
        "OpenGradient/bitquant-app"
    ]
}

# How far back (in days) to look for merged PRs / releases.
# "daily" → 1 day, "weekly" → 7 days.  Override via CLI.
LOOKBACK_DAYS: dict[str, int] = {
    "daily": 1,
    "weekly": 14,
}
