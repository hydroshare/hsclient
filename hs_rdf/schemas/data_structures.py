from datetime import datetime

from pydantic import BaseModel


class BaseCoverage(BaseModel):

    def __str__(self):
        return "; ".join(["=".join([key, val.isoformat() if isinstance(val, datetime) else str(val)])
                          for key, val in self.__dict__.items()
                          if key != "type" and val])


class BoxCoverage(BaseCoverage):
    type: str = "box"
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
    type: str = "point"
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
    start: datetime
    end: datetime
    scheme: str = None