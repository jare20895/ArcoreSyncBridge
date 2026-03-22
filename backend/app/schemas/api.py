from typing import Generic, Optional, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class ApiMeta(BaseModel):
    request_id: Optional[str] = None
    total: Optional[int] = None
    limit: Optional[int] = None
    offset: Optional[int] = None


class ApiResponse(BaseModel, Generic[T]):
    data: T
    meta: ApiMeta


class MessageResponse(BaseModel):
    message: str
