"""MCP tool handlers for research workflow."""

from __future__ import annotations

import asyncio
from typing import Any

from app.core.config import settings
from app.services.mcp.errors import MCPExecutionError, MCPParsingError, MCPRateLimitError, MCPTransportError
from app.services.mcp.reliability import AsyncRateLimiter, AsyncSingleFlight, RetryPolicy, retry_async
from app.schemas.research_agent import ResearchDigestFull
from app.services.research_agent.arxiv_service import search_papers_iterative
from app.services.research_agent.digest_service import generate_research_digest

import logging

logger = logging.getLogger(__name__)


_arxiv_rate_limiter = AsyncRateLimiter(settings.arxiv_min_request_interval_seconds)
_arxiv_singleflight = AsyncSingleFlight()


def score_papers(query: str, papers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Score papers with lightweight keyword relevance, preserving current behavior."""
    query_terms = set(query.lower().split())
    scored: list[dict[str, Any]] = []

    for paper in papers:
        content = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
        matches = sum(1 for term in query_terms if term in content)
        score = matches / len(query_terms) if query_terms else 0.0

        if any(term in paper.get("title", "").lower() for term in query_terms):
            score += 0.2

        updated = dict(paper)
        updated["relevance_score"] = min(score, 1.0)
        scored.append(updated)

    scored.sort(key=lambda p: p.get("relevance_score", 0), reverse=True)
    return scored


async def generate_refined_terms(llm: Any, query: str) -> list[str]:
    """Generate related search terms via existing LLM behavior."""
    prompt = f'''Generate 2-3 related search terms for: "{query}"

Respond with ONLY comma-separated terms, e.g.: "machine learning, neural networks"
Do not include the original query.'''

    if hasattr(llm, "ainvoke"):
        response = await llm.ainvoke(prompt)
    else:
        response = await asyncio.to_thread(llm.invoke, prompt)

    content = response.content if hasattr(response, "content") else str(response)
    return [t.strip() for t in content.split(",") if t.strip()]


class ResearchMCPTools:
    """Collection of research tool handlers exposed by local MCP server."""

    async def search_papers_iterative(
        self,
        query: str,
        max_results: int,
        depth: str,
    ) -> list[dict[str, Any]]:
        key = f"{query.strip().lower()}::{int(max_results)}::{depth}"

        async def _execute_once() -> list[dict[str, Any]]:
            await _arxiv_rate_limiter.acquire()
            papers = await asyncio.to_thread(search_papers_iterative, query, max_results, depth)
            return [paper.to_dict() if hasattr(paper, "to_dict") else paper for paper in papers]

        def _is_retryable(exc: Exception) -> bool:
            return isinstance(exc, (MCPRateLimitError, MCPTransportError, TimeoutError, ConnectionError))

        policy = RetryPolicy(
            max_attempts=max(1, int(settings.arxiv_max_retry_attempts)),
            initial_delay_seconds=max(0.0, float(settings.arxiv_initial_retry_delay_seconds)),
            max_delay_seconds=max(0.0, float(settings.arxiv_max_backoff_delay_seconds)),
            timeout_seconds=max(1.0, float(settings.arxiv_request_timeout_seconds)),
        )

        async def _execute_with_retries() -> list[dict[str, Any]]:
            return await retry_async(
                operation_name="arxiv.search_papers_iterative",
                operation=_execute_once,
                policy=policy,
                is_retryable_error=_is_retryable,
                logger=logger,
            )

        try:
            return await _arxiv_singleflight.do(key, _execute_with_retries)
        except (MCPRateLimitError, MCPTransportError, MCPParsingError) as exc:
            logger.error(
                "arxiv_search_degraded",
                extra={"query": query, "depth": depth, "error": str(exc)},
            )
            # Graceful fallback: return no papers instead of crashing orchestration.
            return []
        except Exception as exc:
            logger.exception("arxiv_search_unexpected_failure")
            raise MCPExecutionError("Research search temporarily unavailable") from exc

    async def score_papers(
        self,
        query: str,
        papers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return await asyncio.to_thread(score_papers, query, papers)

    async def generate_refined_terms(self, llm: Any, query: str) -> list[str]:
        return await generate_refined_terms(llm, query)

    async def generate_digest(
        self,
        query: str,
        papers: list[dict[str, Any]],
        llm: Any,
    ) -> dict[str, Any]:
        digest: ResearchDigestFull = await generate_research_digest(query=query, papers=papers, llm=llm)
        return digest.model_dump()
