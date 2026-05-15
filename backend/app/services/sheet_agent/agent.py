"""
Pandas DataFrame Agent — answers natural language questions about tabular data.

Uses LangChain's create_pandas_dataframe_agent with the project's LiteLLM proxy.
"""

import re
import time
from typing import Optional

import pandas as pd
from fastapi import HTTPException

from app.ai.llm import get_chat_model
from app.schemas.sheet_agent import SheetQueryTableRow


def validate_sheet_agent_dependencies() -> None:
    """Fail fast when sheet-agent runtime dependencies are missing or incompatible."""
    try:
        import tabulate  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Missing required dependency 'tabulate' for spreadsheet queries. "
            "Install it with: pip install tabulate"
        ) from exc

    try:
        from langchain_experimental.agents import create_pandas_dataframe_agent  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "Missing required dependency 'langchain-experimental' for spreadsheet queries. "
            "Install it with: pip install langchain-experimental"
        ) from exc


def _clean_agent_output(raw: str) -> str:
    """Strip any verbose agent scratchpad boilerplate from the final answer."""
    # Trim common LangChain prefixes like "Final Answer:"
    text = re.sub(r"(?i)^(final\s+answer\s*:\s*)", "", raw.strip())
    return text.strip()


def _dataframe_to_table(df: pd.DataFrame, max_rows: int = 200) -> SheetQueryTableRow:
    """Convert a Pandas DataFrame to our wire-format SheetQueryTableRow."""
    cols = list(df.columns)
    rows = []
    for _, row in df.head(max_rows).iterrows():
        rows.append([str(v) if v is not None else "" for v in row.values])
    return SheetQueryTableRow(columns=cols, rows=rows)


def run_sheet_query(
    df: pd.DataFrame,
    question: str,
    max_result_rows: int = 200,
) -> dict:
    """
    Execute a natural-language question against *df* using a Pandas DataFrame Agent.

    Returns a dict with:
      - answer (str)
      - table (SheetQueryTableRow | None)
      - execution_duration_ms (int)
    """
    try:
        validate_sheet_agent_dependencies()
        from langchain_experimental.agents import create_pandas_dataframe_agent  # type: ignore
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    llm = get_chat_model(temperature=0.0)

    try:
        agent = create_pandas_dataframe_agent(
            llm=llm,
            df=df,
            agent_type="openai-tools",
            verbose=False,
            allow_dangerous_code=True,
            max_iterations=10,
            handle_parsing_errors=True,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500, detail=f"Failed to create DataFrame agent: {exc}"
        ) from exc

    start = time.monotonic()
    try:
        raw_answer = agent.invoke({"input": question})
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Agent failed to answer the question: {exc}",
        ) from exc
    elapsed_ms = int((time.monotonic() - start) * 1000)

    # LangChain returns a dict with an "output" key when using invoke()
    if isinstance(raw_answer, dict):
        answer_text = str(raw_answer.get("output", raw_answer))
    else:
        answer_text = str(raw_answer)

    answer_text = _clean_agent_output(answer_text)

    # Attempt to extract any tabular result embedded in the answer
    table: Optional[SheetQueryTableRow] = _try_extract_table(df, answer_text, max_result_rows)

    return {
        "answer": answer_text,
        "table": table,
        "execution_duration_ms": elapsed_ms,
    }


def _try_extract_table(
    df: pd.DataFrame, answer_text: str, max_rows: int
) -> Optional[SheetQueryTableRow]:
    """
    Heuristic: if the answer looks like it contains a DataFrame-like result,
    try to parse it back into a table.  Otherwise return None.
    This is best-effort — the plain-text answer is always the primary output.
    """
    lines = [l.strip() for l in answer_text.splitlines() if l.strip()]

    # Detect a markdown-style table (lines starting with |)
    table_lines = [l for l in lines if l.startswith("|")]
    if len(table_lines) >= 2:
        # First line is headers, second is separator, rest are rows
        header_line = table_lines[0]
        data_lines = [l for l in table_lines[2:] if not re.match(r"^\|[-| ]+\|$", l)]
        cols = [c.strip() for c in header_line.strip("|").split("|")]
        rows = []
        for dl in data_lines[:max_rows]:
            cells = [c.strip() for c in dl.strip("|").split("|")]
            # Pad or trim to match header count
            cells = (cells + [""] * len(cols))[: len(cols)]
            rows.append(cells)
        if cols and rows:
            return SheetQueryTableRow(columns=cols, rows=rows)

    return None
