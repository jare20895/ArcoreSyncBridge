from fastapi import APIRouter, Depends, Request

from app.api.responses import success_response
from app.core.security import Principal, get_current_principal, require_roles
from app.schemas.api import ApiResponse
from app.schemas.auth import PrincipalRead


router = APIRouter()


@router.get("/me", response_model=ApiResponse[PrincipalRead])
def get_me(request: Request, principal: Principal = Depends(get_current_principal)):
    return success_response(request, principal)


@router.get("/admin-check", response_model=ApiResponse[PrincipalRead])
def admin_check(
    request: Request,
    principal: Principal = Depends(require_roles("admin", "platform_admin")),
):
    return success_response(request, principal)
