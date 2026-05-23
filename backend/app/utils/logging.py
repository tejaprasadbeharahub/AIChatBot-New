from __future__ import annotations

import logging


def configure_logging(level: str = "INFO") -> None:
    """Configure a simple structured logging format for API services."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
