"""Scan GitHub repos for recent merged PRs and releases, grouped by product."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from github import Auth, Github


@dataclass
class PRSummary:
    """Lightweight summary of a merged pull request."""

    number: int
    title: str
    body: str
    url: str
    merged_at: datetime
    labels: list[str]
    author: str


@dataclass
class ReleaseSummary:
    """Lightweight summary of a GitHub release."""

    tag: str
    name: str
    body: str
    url: str
    published_at: datetime


@dataclass
class RepoChanges:
    """All notable changes for a single repo in the lookback window."""

    repo_name: str
    prs: list[PRSummary] = field(default_factory=list)
    releases: list[ReleaseSummary] = field(default_factory=list)


@dataclass
class ProductChanges:
    """Aggregated changes across all repos that belong to one product."""

    product_name: str
    repos: list[RepoChanges] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return any(r.prs or r.releases for r in self.repos)

    @property
    def total_prs(self) -> int:
        return sum(len(r.prs) for r in self.repos)


def scan_repos(
    products: dict[str, list[str]],
    lookback_days: int,
    github_token: str,
) -> list[ProductChanges]:
    """Scan all configured repos and return changes grouped by product.

    Args:
        products: mapping of product name → list of "owner/repo" strings.
        lookback_days: how many days back to look for merged PRs / releases.
        github_token: GitHub personal access token (PAT).

    Returns:
        List of ProductChanges, one per product that has at least one change.
    """
    auth = Auth.Token(github_token)
    gh = Github(auth=auth)
    since = datetime.now(timezone.utc) - timedelta(days=lookback_days)

    results: list[ProductChanges] = []

    for product_name, repo_slugs in products.items():
        product = ProductChanges(product_name=product_name)

        for slug in repo_slugs:
            repo = gh.get_repo(slug)
            changes = RepoChanges(repo_name=slug)

            # --- Merged PRs ---
            pulls = repo.get_pulls(state="closed", sort="updated", direction="desc")
            for pr in pulls:
                if pr.merged_at is None:
                    continue
                if pr.merged_at < since:
                    break  # older than our window — stop
                changes.prs.append(
                    PRSummary(
                        number=pr.number,
                        title=pr.title,
                        body=pr.body or "",
                        url=pr.html_url,
                        merged_at=pr.merged_at,
                        labels=[l.name for l in pr.labels],
                        author=pr.user.login if pr.user else "unknown",
                    )
                )

            # --- Releases ---
            for release in repo.get_releases():
                if release.published_at is None:
                    continue
                if release.published_at < since:
                    break
                changes.releases.append(
                    ReleaseSummary(
                        tag=release.tag_name,
                        name=release.title or release.tag_name,
                        body=release.body or "",
                        url=release.html_url,
                        published_at=release.published_at,
                    )
                )

            product.repos.append(changes)

        if product.has_changes:
            results.append(product)

    gh.close()
    return results


def format_changes_for_prompt(products: list[ProductChanges]) -> str:
    """Format scanned changes into a readable text block for the Claude prompt."""
    if not products:
        return "No notable changes found in the lookback window."

    sections: list[str] = []

    for product in products:
        lines: list[str] = [f"## {product.product_name}"]

        for repo in product.repos:
            if not repo.prs and not repo.releases:
                continue
            lines.append(f"\n### Repo: {repo.repo_name}")

            if repo.releases:
                lines.append("\n**Releases:**")
                for rel in repo.releases:
                    lines.append(f"- {rel.name} ({rel.tag}) — {rel.body[:200]}")

            if repo.prs:
                lines.append(f"\n**Merged PRs ({len(repo.prs)}):**")
                for pr in repo.prs:
                    label_str = f" [{', '.join(pr.labels)}]" if pr.labels else ""
                    body_preview = pr.body[:150].replace("\n", " ") if pr.body else ""
                    lines.append(f"- #{pr.number}: {pr.title}{label_str}")
                    if body_preview:
                        lines.append(f"  {body_preview}")

        sections.append("\n".join(lines))

    return "\n\n".join(sections)
