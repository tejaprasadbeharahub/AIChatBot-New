"""
ArXiv API service — searches and retrieves research papers.
"""

import logging
import re
from typing import Optional

import requests
from fastapi import HTTPException

logger = logging.getLogger(__name__)

ARXIV_BASE_URL = "http://export.arxiv.org/api/query"
MAX_RETRIES = 3
TIMEOUT_SECONDS = 10


class ArxivPaper:
    """Represents an arXiv paper."""
    def __init__(
        self,
        arxiv_id: str,
        title: str,
        authors: list[str],
        abstract: str,
        published: str,
        categories: list[str],
        pdf_url: str,
    ):
        self.arxiv_id = arxiv_id
        self.title = title
        self.authors = authors
        self.abstract = abstract
        self.published = published
        self.categories = categories
        self.pdf_url = pdf_url

    def to_dict(self):
        return {
            "arxiv_id": self.arxiv_id,
            "title": self.title,
            "authors": self.authors,
            "abstract": self.abstract,
            "published": self.published,
            "categories": self.categories,
            "pdf_url": self.pdf_url,
        }


def search_papers(
    query: str,
    max_results: int = 10,
    sort_by: str = "relevance",
) -> list[ArxivPaper]:
    """
    Search arXiv for papers matching the query.

    Args:
        query: Search query string
        max_results: Maximum number of papers to return
        sort_by: Sort by 'relevance' or 'lastUpdatedDate'

    Returns:
        List of ArxivPaper objects
    """
    if not query or len(query.strip()) < 3:
        raise HTTPException(status_code=400, detail="Query must be at least 3 characters.")

    # Escape special characters
    query = query.replace('"', "'")

    # Build arXiv query
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": min(max_results, 100),  # arXiv API limit
        "sortBy": sort_by,
        "sortOrder": "descending",
    }

    try:
        response = requests.get(
            ARXIV_BASE_URL,
            params=params,
            timeout=TIMEOUT_SECONDS,
            headers={"User-Agent": "ResearchAgent/1.0 (mailto:research@example.com)"},
        )
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        logger.error(f"ArXiv API error: {exc}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to reach arXiv API: {str(exc)}",
        ) from exc

    papers = _parse_arxiv_response(response.text)
    logger.info(f"Found {len(papers)} papers for query: {query}")
    return papers


def search_papers_iterative(
    query: str,
    max_results: int = 10,
    depth: str = "balanced",
) -> list[ArxivPaper]:
    """
    Search papers with iterative refinement based on depth.

    Args:
        query: Initial search query
        max_results: Maximum total papers to retrieve
        depth: 'quick' (10), 'balanced' (20), 'deep' (50)

    Returns:
        List of ArxivPaper objects
    """
    depth_limits = {
        "quick": 10,
        "balanced": 20,
        "deep": 50,
    }
    limit = min(depth_limits.get(depth, 20), max_results)

    # Try exact match first, then broader search
    papers = search_papers(f'"{query}"', max_results=limit)

    if len(papers) < limit:
        # Try broader search
        broader_results = search_papers(query, max_results=limit)
        # Deduplicate
        seen = {p.arxiv_id for p in papers}
        papers.extend([p for p in broader_results if p.arxiv_id not in seen])

    return papers[:max_results]


def _parse_arxiv_response(response_text: str) -> list[ArxivPaper]:
    """Parse arXiv API XML response."""
    papers = []

    # Extract entries
    entries = re.findall(r"<entry>(.*?)</entry>", response_text, re.DOTALL)

    for entry in entries:
        try:
            # Extract fields
            arxiv_id_match = re.search(r"<id>.*?arxiv\.org/abs/([^<]+)</id>", entry)
            title_match = re.search(r"<title[^>]*>([^<]+)</title>", entry)
            abstract_match = re.search(r"<summary[^>]*>([^<]+)</summary>", entry)
            published_match = re.search(r"<published>([^<]+)</published>", entry)
            category_match = re.search(r'<arxiv:primary_category term="([^"]+)"', entry)

            if not all([arxiv_id_match, title_match, abstract_match, published_match]):
                continue

            arxiv_id = arxiv_id_match.group(1).strip()
            title = title_match.group(1).strip()
            abstract = abstract_match.group(1).strip().replace("\n", " ")
            published = published_match.group(1).strip()
            category = category_match.group(1).strip() if category_match else "unknown"

            # Extract authors
            author_pattern = r"<author>.*?<name>([^<]+)</name>.*?</author>"
            authors = [m.group(1).strip() for m in re.finditer(author_pattern, entry)]

            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

            paper = ArxivPaper(
                arxiv_id=arxiv_id,
                title=title,
                authors=authors,
                abstract=abstract,
                published=published,
                categories=[category],
                pdf_url=pdf_url,
            )
            papers.append(paper)

        except Exception as exc:
            logger.warning(f"Failed to parse entry: {exc}")
            continue

    return papers


def get_paper_details(arxiv_id: str) -> Optional[ArxivPaper]:
    """Get detailed information about a specific paper."""
    try:
        papers = search_papers(f"arxivid:{arxiv_id}", max_results=1)
        return papers[0] if papers else None
    except Exception as exc:
        logger.error(f"Failed to get paper details for {arxiv_id}: {exc}")
        return None
