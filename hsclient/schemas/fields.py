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

    type: RelationType = Field(title="TODO Jeff", description="TODO Jeff")
    value: str = Field(max_length=500, title="TODO Jeff", description="TODO Jeff")

    _parse_relation = root_validator(pre=True)(parse_relation)


class CellInformation(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(default=None, max_length=500, title="TODO Jeff", description="TODO Jeff")
    rows: int = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    columns: int = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    cell_size_x_value: float = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    cell_data_type: str = Field(default=None, max_length=50, title="TODO Jeff", description="TODO Jeff")
    cell_size_y_value: float = Field(default=None, title="TODO Jeff", description="TODO Jeff")


class Rights(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    statement: str = Field(title="TODO Jeff", description="TODO Jeff")
    url: AnyUrl = Field(title="TODO Jeff", description="TODO Jeff")

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

    name: str = Field(default=None, max_length=100, title="TODO Jeff", description="TODO Jeff")

    phone: str = Field(default=None, max_length=25, title="TODO Jeff", description="TODO Jeff")
    address: str = Field(default=None, max_length=250, title="TODO Jeff", description="TODO Jeff")
    organization: str = Field(default=None, max_length=200, title="TODO Jeff", description="TODO Jeff")
    email: EmailStr = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    homepage: HttpUrl = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    description: str = Field(max_length=50, default=None, title="TODO Jeff", description="TODO Jeff")
    identifiers: Dict[UserIdentifierType, AnyUrl] = Field(default={}, title="TODO Jeff", description="TODO Jeff")

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

    name: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    phone: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    address: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    organization: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    email: EmailStr = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    homepage: HttpUrl = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    description: str = Field(max_length=50, default=None, title="TODO Jeff", description="TODO Jeff")
    identifiers: Dict[UserIdentifierType, AnyUrl] = Field(default={}, title="TODO Jeff", description="TODO Jeff")

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

    funding_agency_name: str = Field(title="TODO Jeff", description="TODO Jeff")
    title: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    number: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    funding_agency_url: AnyUrl = Field(default=None, title="TODO Jeff", description="TODO Jeff")


class BandInformation(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(max_length=500, title="TODO Jeff", description="TODO Jeff")
    variable_name: str = Field(default=None, max_length=100, title="TODO Jeff", description="TODO Jeff")
    variable_unit: str = Field(default=None, max_length=50, title="TODO Jeff", description="TODO Jeff")

    no_data_value: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    maximum_value: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    comment: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    method: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    minimum_value: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")


class FieldInformation(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    field_name: str = Field(max_length=128, title="TODO Jeff", description="TODO Jeff")
    field_type: str = Field(max_length=128, title="TODO Jeff", description="TODO Jeff")
    field_type_code: str = Field(default=None, max_length=50, title="TODO Jeff", description="TODO Jeff")
    field_width: int = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    field_precision: int = Field(default=None, title="TODO Jeff", description="TODO Jeff")


class GeometryInformation(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    feature_count: int = Field(default=0, title="TODO Jeff", description="TODO Jeff")
    geometry_type: str = Field(max_length=128, title="TODO Jeff", description="TODO Jeff")


class Variable(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(max_length=1000, title="TODO Jeff", description="TODO Jeff")
    unit: str = Field(max_length=1000, title="TODO Jeff", description="TODO Jeff")
    type: VariableType = Field(title="TODO Jeff", description="TODO Jeff")
    shape: str = Field(max_length=1000, title="TODO Jeff", description="TODO Jeff")
    descriptive_name: str = Field(default=None, max_length=1000, title="TODO Jeff", description="TODO Jeff")
    method: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    missing_value: str = Field(default=None, max_length=1000, title="TODO Jeff", description="TODO Jeff")


class Publisher(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(max_length=200, title="TODO Jeff", description="TODO Jeff")
    url: AnyUrl = Field(title="TODO Jeff", description="TODO Jeff")


class TimeSeriesVariable(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    variable_code: str = Field(max_length=50, title="TODO Jeff", description="TODO Jeff")
    variable_name: str = Field(max_length=100, title="TODO Jeff", description="TODO Jeff")
    variable_type: str = Field(max_length=100, title="TODO Jeff", description="TODO Jeff")
    no_data_value: int = Field(title="TODO Jeff", description="TODO Jeff")
    variable_definition: str = Field(default=None, max_length=255, title="TODO Jeff", description="TODO Jeff")
    speciation: str = Field(default=None, max_length=255, title="TODO Jeff", description="TODO Jeff")


class TimeSeriesSite(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    site_code: str = Field(max_length=200, title="TODO Jeff", description="TODO Jeff")
    site_name: str = Field(default=None, max_length=255, title="TODO Jeff", description="TODO Jeff")
    elevation_m: float = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    elevation_datum: str = Field(default=None, max_length=50, title="TODO Jeff", description="TODO Jeff")
    site_type: str = Field(default=None, max_length=100, title="TODO Jeff", description="TODO Jeff")
    latitude: float = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    longitude: float = Field(default=None, title="TODO Jeff", description="TODO Jeff")


class TimeSeriesMethod(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    method_code: str = Field(max_length=50, title="TODO Jeff", description="TODO Jeff")
    method_name: str = Field(max_length=200, title="TODO Jeff", description="TODO Jeff")
    method_type: str = Field(max_length=200, title="TODO Jeff", description="TODO Jeff")
    method_description: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    method_link: AnyUrl = Field(default=None, title="TODO Jeff", description="TODO Jeff")


class ProcessingLevel(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    processing_level_code: str = Field(max_length=50, title="TODO Jeff", description="TODO Jeff")
    definition: str = Field(default=None, max_length=200, title="TODO Jeff", description="TODO Jeff")
    explanation: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")


class Unit(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: str = Field(max_length=255, title="TODO Jeff", description="TODO Jeff")
    name: str = Field(max_length=255, title="TODO Jeff", description="TODO Jeff")
    abbreviation: str = Field(max_length=20, title="TODO Jeff", description="TODO Jeff")


class UTCOffSet(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    value: float = Field(default=0, title="TODO Jeff", description="TODO Jeff")


class TimeSeriesResult(BaseModel):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    series_id: str = Field(max_length=36, title="TODO Jeff", description="TODO Jeff")
    unit: Unit = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    status: str = Field(default=None, max_length=255, title="TODO Jeff", description="TODO Jeff")
    sample_medium: str = Field(max_length=255, title="TODO Jeff", description="TODO Jeff")
    value_count: int = Field(title="TODO Jeff", description="TODO Jeff")
    aggregation_statistics: str = Field(max_length=255, title="TODO Jeff", description="TODO Jeff")
    series_label: str = Field(default=None, max_length=255, title="TODO Jeff", description="TODO Jeff")
    site: TimeSeriesSite = Field(title="TODO Jeff", description="TODO Jeff")
    variable: TimeSeriesVariable = Field(title="TODO Jeff", description="TODO Jeff")
    method: TimeSeriesMethod = Field(title="TODO Jeff", description="TODO Jeff")
    processing_level: ProcessingLevel = Field(title="TODO Jeff", description="TODO Jeff")
    utc_offset: UTCOffSet = Field(default=None, title="TODO Jeff", description="TODO Jeff")


class BoxCoverage(base_models.BaseCoverage):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: str = Field(default="box", const=True, title="TODO Jeff", description="TODO Jeff")
    name: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    northlimit: float = Field(gt=-90, lt=90, title="TODO Jeff", description="TODO Jeff")
    eastlimit: float = Field(gt=-180, lt=180, title="TODO Jeff", description="TODO Jeff")
    southlimit: float = Field(gt=-90, lt=90, title="TODO Jeff", description="TODO Jeff")
    westlimit: float = Field(gt=-180, lt=180, title="TODO Jeff", description="TODO Jeff")
    units: str = Field(title="TODO Jeff", description="TODO Jeff")
    projection: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")

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

    type: str = Field(default="box", const=True, title="TODO Jeff", description="TODO Jeff")
    name: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    northlimit: float = Field(title="TODO Jeff", description="TODO Jeff")
    eastlimit: float = Field(title="TODO Jeff", description="TODO Jeff")
    southlimit: float = Field(title="TODO Jeff", description="TODO Jeff")
    westlimit: float = Field(title="TODO Jeff", description="TODO Jeff")
    units: str = Field(title="TODO Jeff", description="TODO Jeff")
    projection: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    projection_string: str = Field(title="TODO Jeff", description="TODO Jeff")
    projection_string_type: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    datum: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    projection_name: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")


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

    type: str = Field(default="point", const=True, title="TODO Jeff", description="TODO Jeff")
    name: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    east: float = Field(gt=-180, lt=180, title="TODO Jeff", description="TODO Jeff")
    north: float = Field(gt=-90, lt=90, title="TODO Jeff", description="TODO Jeff")
    units: str = Field(title="TODO Jeff", description="TODO Jeff")
    projection: str = Field(title="TODO Jeff", description="TODO Jeff")


class PointSpatialReference(base_models.BaseCoverage):
    """
    TODO Jeff (description of class)
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: str = Field(default="point", const=True, title="TODO Jeff", description="TODO Jeff")
    name: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    east: float = Field(title="TODO Jeff", description="TODO Jeff")
    north: float = Field(title="TODO Jeff", description="TODO Jeff")
    units: str = Field(title="TODO Jeff", description="TODO Jeff")
    projection: str = Field(title="TODO Jeff", description="TODO Jeff")
    projection_string: str = Field(title="TODO Jeff", description="TODO Jeff")
    projection_string_type: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    projection_name: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")


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

    name: str = Field(default=None, title="TODO Jeff", description="TODO Jeff")
    start: datetime = Field(title="TODO Jeff", description="TODO Jeff")
    end: datetime = Field(title="TODO Jeff", description="TODO Jeff")

    @root_validator
    def start_before_end(cls, values):
        start, end = values["start"], values["end"]
        if start > end:
            raise ValueError(f"start date [{start}] is after end date [{end}]")
        return values
