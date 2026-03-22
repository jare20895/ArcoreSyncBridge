from typing import Any, Optional

from fastapi import Request


def success_response(request: Request, data: Any, meta: Optional[dict[str, Any]] = None):
    return {
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", None),
            **(meta or {}),
        },
    }
