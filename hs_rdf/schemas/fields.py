from __future__ import annotations
from datetime import datetime
from typing import Dict

from pydantic import AnyUrl, Field, HttpUrl, BaseModel, validator, root_validator, EmailStr

from hs_rdf.schemas import base_models
from hs_rdf.schemas.enums import VariableType, RelationType, UserIdentifierType
from hs_rdf.schemas.root_validators import parse_relation, group_user_identifiers
from hs_rdf.schemas.validators import validate_user_url


class User(BaseModel):
    name: str = None
    email: str = None
    url: AnyUrl = None
    phone: str = None
    address: str = None
    organization: str = None
    website: AnyUrl = None
    identifiers: Dict[UserIdentifierType, str] = {}


class Relation(BaseModel):
    type: RelationType
    value: str = Field(max_length=500)

    _parse_relation = root_validator(pre=True)(parse_relation)


class CellInformation(BaseModel):
    name: str = Field(default=None, max_length=500)
    rows: int = Field(default=None)
    columns: int = Field(default=None)
    cell_size_x_value: float = Field(default=None)
    cell_data_type: str = Field(default=None, max_length=50)
    cell_size_y_value: float = Field(default=None)


class Rights(BaseModel):
    statement: str = Field()
    url: AnyUrl = Field()

    @classmethod
    def Creative_Commons_Attribution_CC_BY(cls) -> Rights:
        return Rights(statement="This resource is shared under the Creative Commons Attribution CC BY.",
                      url="http://creativecommons.org/licenses/by/4.0/")

    @classmethod
    def Creative_Commons_Attribution_ShareAlike_CC_BY(cls) -> Rights:
        return Rights(statement="This resource is shared under the Creative Commons Attribution-ShareAlike CC BY-SA.",
                      url="http://creativecommons.org/licenses/by-sa/4.0/")

    @classmethod
    def Creative_Commons_Attribution_NoDerivs_CC_BY_ND(cls) -> Rights:
        return Rights(statement="This resource is shared under the Creative Commons Attribution-ShareAlike CC BY-SA.",
                      url="http://creativecommons.org/licenses/by-nd/4.0/")

    @classmethod
    def Creative_Commons_Attribution_NoCommercial_ShareAlike_CC_BY_NC_SA(cls) -> Rights:
        return Rights(statement="This resource is shared under the Creative Commons Attribution-NoCommercial-ShareAlike"
                                " CC BY-NC-SA.",
                      url="http://creativecommons.org/licenses/by-nc-sa/4.0/")

    @classmethod
    def Creative_Commons_Attribution_NoCommercial_CC_BY_NC(cls) -> Rights:
        return Rights(statement="This resource is shared under the Creative Commons Attribution-NoCommercial CC BY-NC.",
                      url="http://creativecommons.org/licenses/by-nc/4.0/")

    @classmethod
    def Creative_Commons_Attribution_NoCommercial_NoDerivs_CC_BY_NC_ND(cls) -> Rights:
        return Rights(statement="This resource is shared under the Creative Commons Attribution-NoCommercial-NoDerivs "
                                "CC BY-NC-ND.",
                      url="http://creativecommons.org/licenses/by-nc-nd/4.0/")

    @classmethod
    def Other(cls, statement: str, url: EmailStr) -> Rights:
        return Rights(statement=statement, url=url)


class Creator(BaseModel):
    name: str = Field(default=None, max_length=100)

    phone: str = Field(default=None, max_length=25)
    address: str = Field(default=None, max_length=250)
    organization: str = Field(default=None, max_length=200)
    email: EmailStr = Field(default=None)
    homepage: HttpUrl = Field(default=None)
    description: str = Field(max_length=50, default=None)
    identifiers: Dict[UserIdentifierType, AnyUrl] = Field(default={})

    _description_validator = validator("description", pre=True)(validate_user_url)

    _split_identifiers = root_validator(pre=True, allow_reuse=True)(group_user_identifiers)

    @classmethod
    def from_user(cls, user: User) -> Creator:
        user_dict = user.dict()
        user_dict["description"] = user.url.path
        if user.website:
            user_dict["homepage"] = user.website

        return Creator(**user_dict)


class Contributor(BaseModel):
    name: str = Field(default=None)
    phone: str = Field(default=None)
    address: str = Field(default=None)
    organization: str = Field(default=None)
    email: EmailStr = Field(default=None)
    homepage: HttpUrl = Field(default=None)
    identifiers: Dict[UserIdentifierType, AnyUrl] = Field(default={})

    _split_identifiers = root_validator(pre=True, allow_reuse=True)(group_user_identifiers)

    @classmethod
    def from_user(cls, user: User) -> Contributor:
        user_dict = user.dict()
        user_dict["description"] = user.url.path
        if user.website:
            user_dict["homepage"] = user.website

        return Contributor(**user_dict)


class AwardInfo(BaseModel):
    funding_agency_name: str = Field()
    title: str = Field(default=None)
    number: str = Field(default=None)
    funding_agency_url: AnyUrl = Field(default=None)


class BandInformation(BaseModel):
    name: str = Field(max_length=500)
    variable_name: str = Field(default=None, max_length=100)
    variable_unit: str = Field(default=None, max_length=50)

    no_data_value: str = Field(default=None)
    maximum_value: str = Field(default=None)
    comment: str = Field(default=None)
    method: str = Field(default=None)
    minimum_value: str = Field(default=None)


class FieldInformation(BaseModel):
    field_name: str = Field(max_length=128)
    field_type: str = Field(max_length=128)
    field_type_code: str = Field(default=None, max_length=50)
    field_width: int = Field(default=None)
    field_precision: int = Field(default=None)


class GeometryInformation(BaseModel):
    feature_count: int = Field(default=0)
    geometry_type: str = Field(max_length=128)


class Variable(BaseModel):
    name: str = Field(max_length=1000)
    unit: str = Field(max_length=1000)
    type: VariableType = Field()
    shape: str = Field(max_length=1000)
    descriptive_name: str = Field(default=None, max_length=1000)
    method: str = Field(default=None)
    missing_value: str = Field(default=None, max_length=1000)


class Publisher(BaseModel):
    name: str = Field(max_length=200)
    url: AnyUrl = Field()


class TimeSeriesVariable(BaseModel):
    variable_code: str = Field(max_length=50)
    variable_name: str = Field(max_length=100)
    variable_type: str = Field(max_length=100)
    no_data_value: int = Field()
    variable_definition: str = Field(default=None, max_length=255)
    speciation: str = Field(default=None, max_length=255)


class TimeSeriesSite(BaseModel):
    site_code: str = Field(max_length=200)
    site_name: str = Field(default=None, max_length=255)
    elevation_m: float = Field(default=None)
    elevation_datum: str = Field(default=None, max_length=50)
    site_type: str = Field(default=None, max_length=100)
    latitude: float = Field(default=None)
    longitude: float = Field(default=None)


class TimeSeriesMethod(BaseModel):
    method_code: str = Field(max_length=50)
    method_name: str = Field(max_length=200)
    method_type: str = Field(max_length=200)
    method_description: str = Field(default=None)
    method_link: AnyUrl = Field(default=None)


class ProcessingLevel(BaseModel):
    processing_level_code: str = Field(max_length=50)
    definition: str = Field(default=None, max_length=200)
    explanation: str = Field(default=None)


class Unit(BaseModel):
    type: str = Field(max_length=255)
    name: str = Field(max_length=255)
    abbreviation: str = Field(max_length=20)


class UTCOffSet(BaseModel):
    value: float = Field(default=0)


class TimeSeriesResult(BaseModel):
    series_id: str = Field(max_length=36)
    unit: Unit = Field(default=None)
    status: str = Field(default=None, max_length=255)
    sample_medium: str = Field(max_length=255)
    value_count: int = Field()
    aggregation_statistics: str = Field(max_length=255)
    series_label: str = Field(default=None, max_length=255)
    site: TimeSeriesSite = Field()
    variable: TimeSeriesVariable = Field()
    method: TimeSeriesMethod = Field()
    processing_level: ProcessingLevel = Field()
    utc_offset: UTCOffSet = Field(default=None)


class BoxCoverage(base_models.BaseCoverage):
    type: str = Field(default="box", const=True)
    name: str = None
    northlimit: float = Field(gt=-90, lt=90)
    eastlimit: float = Field(gt=-180, lt=180)
    southlimit: float = Field(gt=-90, lt=90)
    westlimit: float = Field(gt=-180, lt=180)
    units: str
    projection: str = None

    @root_validator
    def compare_north_south(cls, values):
        north, south = values["northlimit"], values["southlimit"]
        if north < south:
            raise ValueError(f"North latitude [{north}] must be greater than or equal to South latitude [{south}]")
        return values


class BoxSpatialReference(base_models.BaseCoverage):
    type: str = Field(default="box", const=True)
    name: str = None
    northlimit: float
    eastlimit: float
    southlimit: float
    westlimit: float
    units: str
    projection: str = None
    projection_string: str
    projection_string_type: str = None
    datum: str = None
    projection_name: str = None


class MultidimensionalBoxSpatialReference(BoxSpatialReference):
    pass


class PointCoverage(base_models.BaseCoverage):
    type: str = Field(default="point", const=True)
    name: str = None
    east: float = Field(gt=-180, lt=180)
    north: float = Field(gt=-90, lt=90)
    units: str
    projection: str


class PointSpatialReference(base_models.BaseCoverage):
    type: str = Field(default="point", const=True)
    name: str = None
    east: float
    north: float
    units: str
    projection: str
    projection_string: str
    projection_string_type: str = None
    projection_name: str = None


class MultidimensionalPointSpatialReference(PointSpatialReference):
    pass


class PeriodCoverage(base_models.BaseCoverage):
    name: str = None
    start: datetime
    end: datetime

    @root_validator
    def start_before_end(cls, values):
        start, end = values["start"], values["end"]
        if start > end:
            raise ValueError(f"start date [{start}] is after end date [{end}]")
        return values