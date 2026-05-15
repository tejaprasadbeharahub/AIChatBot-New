"""
Research Agent — orchestrates autonomous research workflow using LangGraph.
"""

import json
import logging
import time
import asyncio
from datetime import datetime, timezone
from typing import Any, Optional

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session
from typing_extensions import TypedDict

from app.ai.llm import get_chat_model
from app.models.research_session import ResearchPaper, ResearchSession
from app.repositories.chat_repo import get_chat_for_user
from app.schemas.research_agent import ResearchDigestFull
from app.services.research_agent.arxiv_service import search_papers_iterative
from app.services.research_agent.digest_service import generate_research_digest

logger = logging.getLogger(__name__)


# State schema for LangGraph workflow
class ResearchState(TypedDict):
    """State maintained throughout research workflow."""
    query: str
    papers: list[dict[str, Any]]
    max_papers: int
    depth: str
    llm: Any
    digest: Optional[ResearchDigestFull]
    error: Optional[str]
    should_continue: bool
    search_attempts: int
    refined_terms: list[str]


class ResearchAgent:
    """Autonomous agent using LangGraph for stateful research workflow."""

    def __init__(self, db: Session, user_id, chat_id):
        self.db = db
        self.user_id = user_id
        self.chat_id = chat_id
        self.llm = get_chat_model(temperature=0.0)
        self.event_callback = None
        self.graph: Optional[Any] = None

    async def research(
        self,
        query: str,
        max_papers: int = 10,
        depth: str = "balanced",
        on_event=None,
    ) -> dict:
        """
        Perform autonomous research using LangGraph workflow.

        Args:
            query: Research question
            max_papers: Maximum papers to collect
            depth: quick, balanced, or deep
            on_event: Callback for streaming events

        Returns:
            Dict with papers and digest
        """
        start_time = time.time()
        self.event_callback = on_event

        try:
            await self._emit_event("searching", {"query": query})

            # Build the LangGraph workflow
            self.graph = self._build_workflow()

            # Initial state
            initial_state = ResearchState(
                query=query,
                papers=[],
                max_papers=max_papers,
                depth=depth,
                llm=self.llm,
                digest=None,
                error=None,
                should_continue=False,
                search_attempts=0,
                refined_terms=[],
            )

            # Run the workflow
            final_state = await self._run_graph(initial_state)

            if final_state.get("error"):
                raise RuntimeError(final_state["error"])

            elapsed = time.time() - start_time

            # Update the digest with the actual search duration
            if final_state.get("digest") is not None:
                final_state["digest"].search_duration_seconds = int(elapsed)

            await self._emit_event("completed", {
                "status": "success",
                "papers_collected": len(final_state["papers"]),
                "duration_seconds": int(elapsed),
            })

            return {
                "query": query,
                "papers": final_state["papers"][:max_papers],
                "digest": final_state["digest"],
                "duration_seconds": int(elapsed),
                "status": "completed",
            }

        except Exception as exc:
            logger.exception("Research failed")
            elapsed = time.time() - start_time
            await self._emit_event("error", {
                "error": str(exc),
                "duration_seconds": int(elapsed),
            })
            raise

    def _build_workflow(self) -> Any:
        """Build the LangGraph workflow."""
        workflow = StateGraph(ResearchState)

        # Add nodes
        workflow.add_node("search_papers", self._node_search_papers)
        workflow.add_node("analyze_papers", self._node_analyze_papers)
        workflow.add_node("decide_continue", self._node_decide_continue)
        workflow.add_node("refine_search", self._node_refine_search)
        workflow.add_node("generate_digest", self._node_generate_digest)
        workflow.add_node("error_handler", self._node_error_handler)

        # Set entry point
        workflow.set_entry_point("search_papers")

        # Add edges with conditions
        workflow.add_edge("search_papers", "analyze_papers")
        workflow.add_edge("analyze_papers", "decide_continue")

        # Conditional edge: if should continue and have room for more papers
        workflow.add_conditional_edges(
            "decide_continue",
            self._should_refine_search,
            {
                "refine": "refine_search",
                "generate": "generate_digest",
            },
        )

        workflow.add_edge("refine_search", "analyze_papers")
        workflow.add_edge("generate_digest", END)
        workflow.add_edge("error_handler", END)

        # Compile the graph
        return workflow.compile()

    async def _run_graph(self, initial_state: ResearchState) -> dict:
        """Run the compiled LangGraph workflow."""
        if self.graph is None:
            raise RuntimeError("Research workflow graph is not initialized")

        # Force async execution path to support async-only nodes like generate_digest.
        final_state: Optional[dict] = None
        async for state in self.graph.astream(initial_state, stream_mode="values"):
            final_state = state

        if final_state is None:
            # Safety fallback in case astream yields no values.
            final_state = await self.graph.ainvoke(initial_state)

        return final_state

    # Graph Nodes
    async def _node_search_papers(self, state: ResearchState) -> dict:
        """Search for papers on arXiv."""
        logger.info(f"Node: Searching papers for '{state['query']}'")

        papers = await asyncio.to_thread(
            search_papers_iterative,
            state["query"],
            state["max_papers"],
            state["depth"],
        )

        # Convert to dicts and emit events
        paper_dicts = []
        for paper in papers:
            paper_dict = paper.to_dict() if hasattr(paper, "to_dict") else paper
            paper_dicts.append(paper_dict)

        # Emit found paper events synchronously
        for paper_dict in paper_dicts:
            await self._emit_event("found_paper", {
                "arxiv_id": paper_dict["arxiv_id"],
                "title": paper_dict["title"],
            })

        state["papers"] = paper_dicts
        state["search_attempts"] = 1
        return state

    async def _node_analyze_papers(self, state: ResearchState) -> dict:
        """Analyze papers for relevance."""
        logger.info(f"Node: Analyzing {len(state['papers'])} papers")

        await self._emit_event("analyzing", {
            "message": f"Analyzing {len(state['papers'])} papers for relevance..."
        })

        self._score_papers_for_relevance(state["query"], state["papers"])
        state["papers"].sort(key=lambda p: p.get("relevance_score", 0), reverse=True)

        return state

    async def _node_decide_continue(self, state: ResearchState) -> dict:
        """Decide if we should continue searching."""
        logger.info("Node: Deciding whether to continue searching")

        should_continue = self._should_continue_searching_sync(
            state["query"],
            state["papers"],
        )

        state["should_continue"] = should_continue
        return state

    async def _node_refine_search(self, state: ResearchState) -> dict:
        """Refine search with related terms."""
        logger.info("Node: Refining search")

        await self._emit_event("searching", {
            "message": "Insufficient evidence - refining search..."
        })

        if not state["refined_terms"]:
            # Generate refined terms
            state["refined_terms"] = await self._generate_refined_terms_async(state["query"])

        # Search with first refined term
        if state["refined_terms"] and state["search_attempts"] < 3:
            term = state["refined_terms"].pop(0)
            refined_papers = await asyncio.to_thread(search_papers_iterative, term, 5, "quick")

            for paper in refined_papers:
                paper_dict = paper.to_dict() if hasattr(paper, "to_dict") else paper
                state["papers"].append(paper_dict)

            state["search_attempts"] += 1

        return state

    async def _node_generate_digest(self, state: ResearchState) -> dict:
        """Generate research digest."""
        logger.info("Node: Generating digest")

        await self._emit_event("generating_digest", {
            "message": f"Generating research digest from {len(state['papers'])} papers..."
        })

        digest = await generate_research_digest(
            query=state["query"],
            papers=state["papers"][:state["max_papers"]],
            llm=state["llm"],
        )

        state["digest"] = digest
        return state

    async def _node_error_handler(self, state: ResearchState) -> dict:
        """Handle errors."""
        logger.error(f"Node: Error - {state.get('error', 'Unknown error')}")
        return state

    # Conditional edges
    def _should_refine_search(self, state: ResearchState) -> str:
        """Determine if we should refine search or generate digest."""
        if (
            state["should_continue"]
            and len(state["papers"]) < state["max_papers"]
            and state["search_attempts"] < 3
        ):
            return "refine"
        return "generate"

    # Helper methods
    def _score_papers_for_relevance(self, query: str, papers: list) -> None:
        """Score papers using keyword matching."""
        query_terms = set(query.lower().split())

        for paper in papers:
            content = f"{paper.get('title', '')} {paper.get('abstract', '')}".lower()
            matches = sum(1 for term in query_terms if term in content)
            score = matches / len(query_terms) if query_terms else 0.0

            if any(term in paper.get("title", "").lower() for term in query_terms):
                score += 0.2

            paper["relevance_score"] = min(score, 1.0)

    def _should_continue_searching_sync(self, query: str, papers: list) -> bool:
        """Decide if we need more papers (sync version)."""
        if not papers or len(papers) < 3:
            return True

        # Check average relevance
        avg_relevance = sum(p.get("relevance_score", 0) for p in papers) / len(papers)
        return avg_relevance < 0.6

    async def _generate_refined_terms_async(self, query: str) -> list[str]:
        """Generate related search terms without blocking the event loop."""
        prompt = f"""Generate 2-3 related search terms for: "{query}"
        
Respond with ONLY comma-separated terms, e.g.: "machine learning, neural networks"
Do not include the original query."""

        try:
            if hasattr(self.llm, "ainvoke"):
                response = await self.llm.ainvoke(prompt)
            else:
                response = await asyncio.to_thread(self.llm.invoke, prompt)

            content = response.content if hasattr(response, "content") else str(response)
            terms = [t.strip() for t in content.split(",") if t.strip()]
            logger.info(f"Refined terms: {terms}")
            return terms
        except Exception as exc:
            logger.warning(f"Failed to generate refined terms: {exc}")
            return []

    async def _emit_event(self, event_type: str, data: dict) -> None:
        """Emit streaming event (async version)."""
        if self.event_callback:
            try:
                await self.event_callback({
                    "event_type": event_type,
                    "data": data,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            except Exception as exc:
                logger.error(f"Failed to emit event: {exc}")


def validate_research_agent_dependencies() -> None:
    """Fail fast if dependencies are missing."""
    try:
        import requests  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Missing 'requests' package for arXiv API. Install: pip install requests"
        ) from exc
