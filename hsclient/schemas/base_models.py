from datetime import datetime

from pydantic import BaseModel


class BaseMetadata(BaseModel):
    class Config:
        validate_assignment = True


class BaseCoverage(BaseMetadata):
    def __str__(self):
        return "; ".join(
            [
                "=".join([key, val.isoformat() if isinstance(val, datetime) else str(val)])
                for key, val in self.__dict__.items()
                if key != "type" and val
            ]
        )
