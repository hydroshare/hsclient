from datetime import datetime
from typing import Dict

from pydantic import BaseModel, AnyUrl, Field, root_validator

from hs_rdf.schemas.enums import UserIdentifierType


class BaseCoverage(BaseModel):

    def __str__(self):
        return "; ".join(["=".join([key, val.isoformat() if isinstance(val, datetime) else str(val)])
                          for key, val in self.__dict__.items()
                          if key != "type" and val])


class BoxCoverage(BaseCoverage):
    type: str = Field(default="box", const=True)
    name: str = None
    northlimit: float
    eastlimit: float
    southlimit: float
    westlimit: float
    units: str
    projection: str = None


class BoxSpatialReference(BoxCoverage):
    projection_string: str
    projection_string_type: str = None
    datum: str = None
    projection_name: str = None


class MultidimensionalBoxSpatialReference(BoxSpatialReference):
    pass


class PointCoverage(BaseCoverage):
    type: str = Field(default="point", const=True)
    name: str = None
    east: float
    north: float
    units: str
    projection: str


class PointSpatialReference(PointCoverage):
    projection_string: str
    projection_string_type: str = None
    projection_name: str = None


class MultidimensionalPointSpatialReference(PointSpatialReference):
    pass


class PeriodCoverage(BaseCoverage):
    name: str = None
    start: datetime
    end: datetime

    @root_validator
    def start_before_end(cls, values):
        start, end = values["start"], values["end"]
        if start > end:
            raise ValueError(f"start date [{start}] is after end date [{end}]")
        return values


class User(BaseModel):
    name: str = None
    email: str = None
    url: AnyUrl = None
    phone: str = None
    address: str = None
    organization: str = None
    website: AnyUrl = None
    identifiers: Dict[UserIdentifierType, str] = {}
