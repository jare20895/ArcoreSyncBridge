from pydantic import BaseModel


class PrincipalRead(BaseModel):
    email: str
    role: str
    auth_mode: str
