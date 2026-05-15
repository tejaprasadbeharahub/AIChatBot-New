"""
Digest generation — creates structured research summaries from papers.
"""

import json
import logging
import asyncio
from typing import Any

from app.schemas.research_agent import (
    ResearchDigestFull,
    ResearchDigestKeyFinding,
    ResearchDigestMethodology,
    ResearchDigestTrend,
    ResearchPaperRef,
)

logger = logging.getLogger(__name__)


async def _invoke_llm_async(llm: Any, prompt: str) -> Any:
    """Invoke LLM asynchronously with fallback for sync-only clients."""
    if hasattr(llm, "ainvoke"):
        return await llm.ainvoke(prompt)
    return await asyncio.to_thread(llm.invoke, prompt)


def _response_to_text(response: Any) -> str:
    """Normalize different LLM response types to text."""
    if hasattr(response, "content"):
        return str(response.content).strip()
    return str(response).strip()


async def generate_research_digest(
    query: str,
    papers: list[dict[str, Any]],
    llm: Any,
) -> ResearchDigestFull:
    """
    Generate a structured research digest from papers using LLM.

    Args:
        query: Original research query
        papers: List of paper dictionaries
        llm: Language model instance

    Returns:
        ResearchDigestFull with structured digest
    """
    if not papers:
        raise ValueError("No papers provided for digest generation")

    # Create paper context
    papers_text = "\n\n".join([
        f"Paper {i+1}: {p['title']}\n"
        f"Authors: {', '.join(p['authors'][:3])}\n"
        f"Abstract: {p['abstract'][:500]}...\n"
        f"ArXiv: {p['arxiv_id']}"
        for i, p in enumerate(papers[:10])
    ])

    # Generate key findings
    findings_prompt = f"""Analyze these research papers and identify 3-5 key findings:

Question: {query}

Papers:
{papers_text}

Respond with JSON array of findings (5-10 sentences each):
[
  {{"topic": "...", "finding": "...", "evidence_papers": ["arxiv_id1", "arxiv_id2"]}},
  ...
]

Include ONLY valid JSON, no other text."""

    key_findings = await _extract_json_array(llm, findings_prompt, "findings")

    # Generate summary
    summary_prompt = f"""Write a 2-3 paragraph research summary:

Question: {query}

Papers ({len(papers)} total):
{papers_text[:2000]}

Focus on: main contributions, current state, open questions.
Be concise and evidence-based."""

    summary = await _get_llm_response(llm, summary_prompt)

    # Extract methodologies
    methodologies_prompt = f"""List common research methodologies in 2-3 items:

Papers:
{papers_text}

Respond as JSON:
[
  {{"name": "...", "frequency": 3, "papers": ["id1", "id2"]}},
  ...
]

ONLY valid JSON."""

    methodologies = await _extract_json_array(llm, methodologies_prompt, "methodologies")

    # Identify limitations
    limitations_prompt = f"""List 3-4 key limitations mentioned or implied:

Research: {query}

Papers:
{papers_text}

Respond as JSON array of strings:
["limitation1", "limitation2", ...]

ONLY valid JSON."""

    limitations = await _extract_json_array(llm, limitations_prompt, "limitations")

    # Identify trends
    trends_prompt = f"""Identify 2-3 research trends:

Topic: {query}

Papers:
{papers_text}

Respond as JSON:
[
  {{"trend": "...", "direction": "increasing|decreasing|stable", "recent_papers": ["id1"]}},
  ...
]

ONLY valid JSON."""

    trends = await _extract_json_array(llm, trends_prompt, "trends")

    # Build digest
    digest = ResearchDigestFull(
        summary=summary,
        key_findings=[
            ResearchDigestKeyFinding(**f) for f in key_findings
        ] if key_findings else [],
        methodologies=[
            ResearchDigestMethodology(**m) for m in methodologies
        ] if methodologies else [],
        limitations=limitations if isinstance(limitations, list) else [],
        trends=[
            ResearchDigestTrend(**t) for t in trends
        ] if trends else [],
        total_papers_reviewed=len(papers),
        papers_cited=[
            ResearchPaperRef(
                arxiv_id=p["arxiv_id"],
                title=p["title"],
                authors=p["authors"],
                abstract=p["abstract"][:300],
                published_date=p["published"],
                categories=p["categories"],
                pdf_url=p["pdf_url"],
                relevance_score=p.get("relevance_score", 0.5),
            )
            for p in papers
        ],
        search_duration_seconds=0,  # Set by caller
    )

    return digest


async def _get_llm_response(llm: Any, prompt: str) -> str:
    """Get a simple text response from LLM."""
    try:
        response = await _invoke_llm_async(llm, prompt)
        return _response_to_text(response)
    except Exception as exc:
        logger.error(f"LLM response failed: {exc}")
        return "Unable to generate response"


async def _extract_json_array(
    llm: Any,
    prompt: str,
    field_name: str,
) -> list[dict[str, Any]]:
    """Extract JSON array from LLM response."""
    try:
        response = await _invoke_llm_async(llm, prompt)
        text = _response_to_text(response)

        # Find JSON array in response
        import re
        match = re.search(r"\[.*\]", text, re.DOTALL)
        if not match:
            logger.warning(f"No JSON found in response for {field_name}")
            return []

        json_str = match.group(0)
        result = json.loads(json_str)
        if isinstance(result, list):
            return result
        logger.warning(f"JSON payload for {field_name} was not a list")
        return []

    except json.JSONDecodeError as exc:
        logger.error(f"Failed to parse JSON for {field_name}: {exc}")
        return []
    except Exception as exc:
        logger.error(f"Failed to extract {field_name}: {exc}")
        return []
