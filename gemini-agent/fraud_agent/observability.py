from __future__ import annotations

import json
import logging
import time
from contextlib import contextmanager
from typing import Iterator

logger = logging.getLogger("fraud_agent.pipeline")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format="%(message)s")


@contextmanager
def trace_stage(case_id: str, component: str) -> Iterator[None]:
    start = time.perf_counter()
    error = ""
    status = "success"
    try:
        yield
    except Exception as exc:
        status = "error"
        error = str(exc)
        raise
    finally:
        duration_ms = round((time.perf_counter() - start) * 1000, 3)
        logger.info(
            json.dumps(
                {
                    "case_id": case_id,
                    "component": component,
                    "status": status,
                    "duration_ms": duration_ms,
                    "error": error,
                },
                sort_keys=True,
            )
        )
