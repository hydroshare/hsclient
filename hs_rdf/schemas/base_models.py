from pydantic import BaseModel


class BaseMetadata(BaseModel):

    class Config:
        validate_assignment = True
