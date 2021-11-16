# typing imports
from typing import Optional

from pydantic import BaseModel


# see rfc 6749 https://datatracker.ietf.org/doc/html/rfc6749#section-4.2.2
class Token(BaseModel):
    access_token: str
    token_type: str
    scope: Optional[str]
    state: Optional[str]
    expires_in: Optional[int]
    refresh_token: Optional[str]

    class Config:
        # do not allow extra fields
        extra = "forbid"
