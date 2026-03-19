from typing import Any

from fastapi import Request


def success_response(request: Request, data: Any):
    return {
        "data": data,
        "meta": {
            "request_id": getattr(request.state, "request_id", None),
        },
    }
