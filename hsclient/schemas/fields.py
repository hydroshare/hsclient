from datetime import datetime
from typing import Dict

from pydantic import AnyUrl, BaseModel, EmailStr, Field, HttpUrl, root_validator, validator

from hsclient.schemas import base_models
from hsclient.schemas.enums import RelationType, UserIdentifierType, VariableType
from hsclient.schemas.json_models import User
from hsclient.schemas.root_validators import group_user_identifiers, parse_relation
from hsclient.schemas.validators import validate_user_url


class Relation(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: RelationType = Field(description="TODO Jeff", title="TODO Jeff")
    value: str = Field(max_length=500, description="TODO Jeff", title="TODO Jeff")

    _parse_relation = root_validator(pre=True)(parse_relation)


class CellInformation(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(default=None, max_length=500, description="TODO Jeff", title="TODO Jeff")
    rows: int = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    columns: int = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    cell_size_x_value: float = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    cell_data_type: str = Field(default=None, max_length=50, description="TODO Jeff", title="TODO Jeff")
    cell_size_y_value: float = Field(default=None, description="TODO Jeff", title="TODO Jeff")


class Rights(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    statement: str = Field(description="TODO Jeff", title="TODO Jeff")
    url: AnyUrl = Field(description="TODO Jeff", title="TODO Jeff")

    @classmethod
    def Creative_Commons_Attribution_CC_BY(cls):
        return Rights(
            statement="This resource is shared under the Creative Commons Attribution CC BY.",
            url="http://creativecommons.org/licenses/by/4.0/",
        )

    @classmethod
    def Creative_Commons_Attribution_ShareAlike_CC_BY(cls):
        return Rights(
            statement="This resource is shared under the Creative Commons Attribution-ShareAlike CC BY-SA.",
            url="http://creativecommons.org/licenses/by-sa/4.0/",
        )

    @classmethod
    def Creative_Commons_Attribution_NoDerivs_CC_BY_ND(cls):
        return Rights(
            statement="This resource is shared under the Creative Commons Attribution-ShareAlike CC BY-SA.",
            url="http://creativecommons.org/licenses/by-nd/4.0/",
        )

    @classmethod
    def Creative_Commons_Attribution_NoCommercial_ShareAlike_CC_BY_NC_SA(cls):
        return Rights(
            statement="This resource is shared under the Creative Commons Attribution-NoCommercial-ShareAlike"
            " CC BY-NC-SA.",
            url="http://creativecommons.org/licenses/by-nc-sa/4.0/",
        )

    @classmethod
    def Creative_Commons_Attribution_NoCommercial_CC_BY_NC(cls):
        return Rights(
            statement="This resource is shared under the Creative Commons Attribution-NoCommercial CC BY-NC.",
            url="http://creativecommons.org/licenses/by-nc/4.0/",
        )

    @classmethod
    def Creative_Commons_Attribution_NoCommercial_NoDerivs_CC_BY_NC_ND(cls):
        return Rights(
            statement="This resource is shared under the Creative Commons Attribution-NoCommercial-NoDerivs "
            "CC BY-NC-ND.",
            url="http://creativecommons.org/licenses/by-nc-nd/4.0/",
        )

    @classmethod
    def Other(cls, statement: str, url: EmailStr):
        return Rights(statement=statement, url=url)


class Creator(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(default=None, max_length=100, description="TODO Jeff", title="TODO Jeff")

    phone: str = Field(default=None, max_length=25, description="TODO Jeff", title="TODO Jeff")
    address: str = Field(default=None, max_length=250, description="TODO Jeff", title="TODO Jeff")
    organization: str = Field(default=None, max_length=200, description="TODO Jeff", title="TODO Jeff")
    email: EmailStr = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    homepage: HttpUrl = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    description: str = Field(max_length=50, default=None, description="TODO Jeff", title="TODO Jeff")
    identifiers: Dict[UserIdentifierType, AnyUrl] = Field(default={}, description="TODO Jeff", title="TODO Jeff")

    _description_validator = validator("description", pre=True)(validate_user_url)

    _split_identifiers = root_validator(pre=True, allow_reuse=True)(group_user_identifiers)

    @classmethod
    def from_user(cls, user: User):
        user_dict = user.dict()
        user_dict["description"] = user.url.path
        if user.website:
            user_dict["homepage"] = user.website

        return Creator(**user_dict)


class Author(Creator):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    pass


class Contributor(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    phone: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    address: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    organization: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    email: EmailStr = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    homepage: HttpUrl = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    description: str = Field(max_length=50, default=None, description="TODO Jeff", title="TODO Jeff")
    identifiers: Dict[UserIdentifierType, AnyUrl] = Field(default={}, description="TODO Jeff", title="TODO Jeff")

    _split_identifiers = root_validator(pre=True, allow_reuse=True)(group_user_identifiers)

    @classmethod
    def from_user(cls, user: User):
        """
        Constructs a Contributor from a User object
        :param user: a User
        :return: a Contributor
        """
        user_dict = user.dict()
        user_dict["description"] = user.url.path
        if user.website:
            user_dict["homepage"] = user.website

        return Contributor(**user_dict)


class AwardInfo(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    funding_agency_name: str = Field(description="TODO Jeff", title="TODO Jeff")
    title: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    number: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    funding_agency_url: AnyUrl = Field(default=None, description="TODO Jeff", title="TODO Jeff")


class BandInformation(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(max_length=500, description="TODO Jeff", title="TODO Jeff")
    variable_name: str = Field(default=None, max_length=100, description="TODO Jeff", title="TODO Jeff")
    variable_unit: str = Field(default=None, max_length=50, description="TODO Jeff", title="TODO Jeff")

    no_data_value: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    maximum_value: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    comment: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    method: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    minimum_value: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")


class FieldInformation(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    field_name: str = Field(max_length=128, description="TODO Jeff", title="TODO Jeff")
    field_type: str = Field(max_length=128, description="TODO Jeff", title="TODO Jeff")
    field_type_code: str = Field(default=None, max_length=50, description="TODO Jeff", title="TODO Jeff")
    field_width: int = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    field_precision: int = Field(default=None, description="TODO Jeff", title="TODO Jeff")


class GeometryInformation(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    feature_count: int = Field(default=0, description="TODO Jeff", title="TODO Jeff")
    geometry_type: str = Field(max_length=128, description="TODO Jeff", title="TODO Jeff")


class Variable(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(max_length=1000, description="TODO Jeff", title="TODO Jeff")
    unit: str = Field(max_length=1000, description="TODO Jeff", title="TODO Jeff")
    type: VariableType = Field(description="TODO Jeff", title="TODO Jeff")
    shape: str = Field(max_length=1000, description="TODO Jeff", title="TODO Jeff")
    descriptive_name: str = Field(default=None, max_length=1000, description="TODO Jeff", title="TODO Jeff")
    method: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    missing_value: str = Field(default=None, max_length=1000, description="TODO Jeff", title="TODO Jeff")


class Publisher(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(max_length=200, description="TODO Jeff", title="TODO Jeff")
    url: AnyUrl = Field(description="TODO Jeff", title="TODO Jeff")


class TimeSeriesVariable(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    variable_code: str = Field(max_length=50, description="TODO Jeff", title="TODO Jeff")
    variable_name: str = Field(max_length=100, description="TODO Jeff", title="TODO Jeff")
    variable_type: str = Field(max_length=100, description="TODO Jeff", title="TODO Jeff")
    no_data_value: int = Field(description="TODO Jeff", title="TODO Jeff")
    variable_definition: str = Field(default=None, max_length=255, description="TODO Jeff", title="TODO Jeff")
    speciation: str = Field(default=None, max_length=255, description="TODO Jeff", title="TODO Jeff")


class TimeSeriesSite(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    site_code: str = Field(max_length=200, description="TODO Jeff", title="TODO Jeff")
    site_name: str = Field(default=None, max_length=255, description="TODO Jeff", title="TODO Jeff")
    elevation_m: float = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    elevation_datum: str = Field(default=None, max_length=50, description="TODO Jeff", title="TODO Jeff")
    site_type: str = Field(default=None, max_length=100, description="TODO Jeff", title="TODO Jeff")
    latitude: float = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    longitude: float = Field(default=None, description="TODO Jeff", title="TODO Jeff")


class TimeSeriesMethod(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    method_code: str = Field(max_length=50, description="TODO Jeff", title="TODO Jeff")
    method_name: str = Field(max_length=200, description="TODO Jeff", title="TODO Jeff")
    method_type: str = Field(max_length=200, description="TODO Jeff", title="TODO Jeff")
    method_description: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    method_link: AnyUrl = Field(default=None, description="TODO Jeff", title="TODO Jeff")


class ProcessingLevel(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    processing_level_code: str = Field(max_length=50, description="TODO Jeff", title="TODO Jeff")
    definition: str = Field(default=None, max_length=200, description="TODO Jeff", title="TODO Jeff")
    explanation: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")


class Unit(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: str = Field(max_length=255, description="TODO Jeff", title="TODO Jeff")
    name: str = Field(max_length=255, description="TODO Jeff", title="TODO Jeff")
    abbreviation: str = Field(max_length=20, description="TODO Jeff", title="TODO Jeff")


class UTCOffSet(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    value: float = Field(default=0, description="TODO Jeff", title="TODO Jeff")


class TimeSeriesResult(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    series_id: str = Field(max_length=36, description="TODO Jeff", title="TODO Jeff")
    unit: Unit = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    status: str = Field(default=None, max_length=255, description="TODO Jeff", title="TODO Jeff")
    sample_medium: str = Field(max_length=255, description="TODO Jeff", title="TODO Jeff")
    value_count: int = Field(description="TODO Jeff", title="TODO Jeff")
    aggregation_statistics: str = Field(max_length=255, description="TODO Jeff", title="TODO Jeff")
    series_label: str = Field(default=None, max_length=255, description="TODO Jeff", title="TODO Jeff")
    site: TimeSeriesSite = Field(description="TODO Jeff", title="TODO Jeff")
    variable: TimeSeriesVariable = Field(description="TODO Jeff", title="TODO Jeff")
    method: TimeSeriesMethod = Field(description="TODO Jeff", title="TODO Jeff")
    processing_level: ProcessingLevel = Field(description="TODO Jeff", title="TODO Jeff")
    utc_offset: UTCOffSet = Field(default=None, description="TODO Jeff", title="TODO Jeff")


class BoxCoverage(base_models.BaseCoverage):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: str = Field(default="box", const=True, description="TODO Jeff", title="TODO Jeff")
    name: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    northlimit: float = Field(gt=-90, lt=90, description="TODO Jeff", title="TODO Jeff")
    eastlimit: float = Field(gt=-180, lt=180, description="TODO Jeff", title="TODO Jeff")
    southlimit: float = Field(gt=-90, lt=90, description="TODO Jeff", title="TODO Jeff")
    westlimit: float = Field(gt=-180, lt=180, description="TODO Jeff", title="TODO Jeff")
    units: str = Field(description="TODO Jeff", title="TODO Jeff")
    projection: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")

    @root_validator
    def compare_north_south(cls, values):
        north, south = values["northlimit"], values["southlimit"]
        if north < south:
            raise ValueError(f"North latitude [{north}] must be greater than or equal to South latitude [{south}]")
        return values


class BoxSpatialReference(base_models.BaseCoverage):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: str = Field(default="box", const=True, description="TODO Jeff", title="TODO Jeff")
    name: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    northlimit: float = Field(description="TODO Jeff", title="TODO Jeff")
    eastlimit: float = Field(description="TODO Jeff", title="TODO Jeff")
    southlimit: float = Field(description="TODO Jeff", title="TODO Jeff")
    westlimit: float = Field(description="TODO Jeff", title="TODO Jeff")
    units: str = Field(description="TODO Jeff", title="TODO Jeff")
    projection: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    projection_string: str = Field(description="TODO Jeff", title="TODO Jeff")
    projection_string_type: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    datum: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    projection_name: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")


class MultidimensionalBoxSpatialReference(BoxSpatialReference):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'


class PointCoverage(base_models.BaseCoverage):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: str = Field(default="point", const=True, description="TODO Jeff", title="TODO Jeff")
    name: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    east: float = Field(gt=-180, lt=180, description="TODO Jeff", title="TODO Jeff")
    north: float = Field(gt=-90, lt=90, description="TODO Jeff", title="TODO Jeff")
    units: str = Field(description="TODO Jeff", title="TODO Jeff")
    projection: str = Field(description="TODO Jeff", title="TODO Jeff")


class PointSpatialReference(base_models.BaseCoverage):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: str = Field(default="point", const=True, description="TODO Jeff", title="TODO Jeff")
    name: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    east: float = Field(description="TODO Jeff", title="TODO Jeff")
    north: float = Field(description="TODO Jeff", title="TODO Jeff")
    units: str = Field(description="TODO Jeff", title="TODO Jeff")
    projection: str = Field(description="TODO Jeff", title="TODO Jeff")
    projection_string: str = Field(description="TODO Jeff", title="TODO Jeff")
    projection_string_type: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    projection_name: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")


class MultidimensionalPointSpatialReference(PointSpatialReference):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'


class PeriodCoverage(base_models.BaseCoverage):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(default=None, description="TODO Jeff", title="TODO Jeff")
    start: datetime = Field(description="TODO Jeff", title="TODO Jeff")
    end: datetime = Field(description="TODO Jeff", title="TODO Jeff")

    @root_validator
    def start_before_end(cls, values):
        start, end = values["start"], values["end"]
        if start > end:
            raise ValueError(f"start date [{start}] is after end date [{end}]")
        return values
