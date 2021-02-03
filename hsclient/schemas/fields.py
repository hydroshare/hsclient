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
    A class used to represent the metadata associated with a resource related to the resource being described
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: RelationType = Field(title="Relation type", description="The type of relationship with the related resource")
    value: str = Field(max_length=500, title="Value", description="String expressing the Full text citation, URL link for, or description of the related resource")

    _parse_relation = root_validator(pre=True)(parse_relation)


class CellInformation(BaseModel):
    """
    A class used to represent the metadata associated with raster grid cells in geographic raster aggregations
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    # TODO: Is there such a thing as name for CellInformation
    name: str = Field(default=None, max_length=500, title="TODO Jeff", description="TODO Jeff")
    rows: int = Field(default=None, title="Rows", description="The integer number of rows in the raster dataset")
    columns: int = Field(default=None, title="Columns", description="The integer number of columns in the raster dataset")
    cell_size_x_value: float = Field(default=None, title="Cell size x value", description="The size of the raster grid cell in the x-direction expressed as a float")
    cell_data_type: str = Field(default=None, max_length=50, title="Cell data type", description="The data type of the raster grid cell values")
    cell_size_y_value: float = Field(default=None, title="Cell size y value", description="The size of the raster grid cell in the y-direction expressed as a float")


class Rights(BaseModel):
    """
    A class used to represent the rights statement metadata associated with a resource
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    statement: str = Field(title="Statement", description="A string containing the text of the license or rights statement")
    url: AnyUrl = Field(title="URL", description="An object containing the URL pointing to a description of the license or rights statement")

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
    A class used to represent the metadata associated with a creator of a resource
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(default=None, max_length=100, title="Name", description="A string containing the name of the creator")
    phone: str = Field(default=None, max_length=25, title="Phone", description="A string containing a phone number for the creator")
    address: str = Field(default=None, max_length=250, title="Address", description="A string containing an address for the creator")
    organization: str = Field(default=None, max_length=200, title="Organization", description="A string containing the name of the organization with which the creator is affiliated")
    email: EmailStr = Field(default=None, title="Email", description="A string containing an email address for the creator")
    homepage: HttpUrl = Field(default=None, title="Homepage", description="An object containing the URL for website associated with the creator")
    # TODO: Is there such a thing as a description property for Creator?
    description: str = Field(max_length=50, default=None, title="Description", description="A string containing a description of the creator")
    identifiers: Dict[UserIdentifierType, AnyUrl] = Field(default={}, title="Creator identifiers", description="A dictionary containing identifier types and URL links to alternative identiers for the creator")

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
    A class used to represent the metadata associated with an author of a resource
    TODO: How is this different than the Creator class, and what is it used for?
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    pass


class Contributor(BaseModel):
    """
    A class used to represent the metadata associated with a contributor to a resource
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(default=None, title="Name", description="A string containing the name of the contributor")
    phone: str = Field(default=None, title="Phone", description="A string containing a phone number for the contributor")
    address: str = Field(default=None, title="Address", description="A string containing an address for the contributor")
    organization: str = Field(default=None, title="Organization", description="A string containing the name of the organization with which the contributor is affiliated")
    email: EmailStr = Field(default=None, title="Email", description="A string containing an email address for the contributor")
    homepage: HttpUrl = Field(default=None, title="Homepage", description="An object containing the URL for website associated with the contributor")
    # TODO: is there such a thing as a description property for contributor?
    description: str = Field(max_length=50, default=None, title="Description", description="A string containing a description of the contributor")
    identifiers: Dict[UserIdentifierType, AnyUrl] = Field(default={}, title="Contributor identifiers", description="A dictionary containing identifier types and URL links to alternative identiers for the contributor")

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
    A class used to represent the metadata associated with funding agency credits for a resource
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    funding_agency_name: str = Field(title="Agency name", description="A string containing the name of the funding agency or organization")
    title: str = Field(default=None, title="Award title", description="A string containing the title of the project or award")
    number: str = Field(default=None, title="Award number", description="A string containing the award number or other identifier")
    funding_agency_url: AnyUrl = Field(default=None, title="Agency URL", description="An object containing a URL pointing to a website describing the funding award")


class BandInformation(BaseModel):
    """
    A class used to represent the metadata associated with the raster bands of a geographic raster aggregation
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(max_length=500, title="Name", description="A string containing the name of the raster band")
    variable_name: str = Field(default=None, max_length=100, title="Variable name", description="A string containing the name of the variable represented by the raster band")
    variable_unit: str = Field(default=None, max_length=50, title="Variable unit", description="A string containing the units for the raster band variable")
    no_data_value: str = Field(default=None, title="Nodata value", description="A string containing the numeric nodata value for the raster band")
    maximum_value: str = Field(default=None, title="Maximum value", description="A string containing the maximum numeric value for the raster band")
    comment: str = Field(default=None, title="Comment", description="A string containing a comment about the raster band")
    method: str = Field(default=None, title="Method", description="A string containing a description of the method used to create the raster band data")
    minimum_value: str = Field(default=None, title="Minimum value", description="A string containing the minimum numerica value for the raster dataset")


class FieldInformation(BaseModel):
    """
    A class used to represent the metadata associated with a field in the attribute table for a geographic feature aggregation
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    field_name: str = Field(max_length=128, title="Field name", description="A string containing the name of the attribute table field")
    field_type: str = Field(max_length=128, title="Field type", description="A string containing the data type of the values in the field")
    # TODO: What is the field_type_code? It's not displayed on the resource landing page, but it's encoded in the
    #  aggregation metadata as an integer value.
    field_type_code: str = Field(default=None, max_length=50, title="Field type code", description="A string value containing a code that indicates the field type")
    field_width: int = Field(default=None, title="Field width", description="An integer value containing the width of the attribute field")
    field_precision: int = Field(default=None, title="Field precision", description="An integer value containing the precision of the attribute field")


class GeometryInformation(BaseModel):
    """
    A class used to represent the metadata associated with the geometry of a geographic feature aggregation
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    feature_count: int = Field(default=0, title="Feature count", description="An integer containing the number of features in the geographic feature aggregation")
    geometry_type: str = Field(max_length=128, title="Geometry type", description="A string containing the type of features in the geographic feature aggregation")


class Variable(BaseModel):
    """
    A class used to represent the metadata associated with a variable contained within a multidimensional aggregation
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(max_length=1000, title="Variable name", description="A string containing the name of the variable")
    unit: str = Field(max_length=1000, title="Units", description="A string containing the units in which the values for the variable are expressed")
    type: VariableType = Field(title="Type", description="The data type of the values for the variable")
    shape: str = Field(max_length=1000, title="Shape", description="A string containing the shape of the variable expressed as a list of dimensions")
    descriptive_name: str = Field(default=None, max_length=1000, title="Descriptive name", description="A string containing a descriptive name for the variable")
    method: str = Field(default=None, title="Method", description="A string containing a description of the method used to create the values for the variable")
    missing_value: str = Field(default=None, max_length=1000, title="Missing value", description="A string containing the value used to indicate missing values for the variable")


class Publisher(BaseModel):
    """
    A class used to represent the metadata associated with the publisher of a resource
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    name: str = Field(max_length=200, title="Publisher name", description="A string containing the name of the publisher")
    url: AnyUrl = Field(title="Publisher URL", description="An object containing a URL that points to the publisher website")


class TimeSeriesVariable(BaseModel):
    """
    A class used to represent the metadata associated with a variable contained within a time series aggregation
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    variable_code: str = Field(max_length=50, title="Variable code", description="A string containing a short but meaningful code that identifies a variable")
    variable_name: str = Field(max_length=100, title="Variable name", description="A string containing the name of the variable")
    variable_type: str = Field(max_length=100, title="Variable type", description="A string containing the type of variable from the ODM2 VariableType controlled vocabulary")
    # TODO: The NoData value for a variable in an ODM2 database is not always an integer.
    #  It could be a floating point value. We might want to change this to a string
    no_data_value: int = Field(title="NoData value", description="The NoData value for the variable")
    variable_definition: str = Field(default=None, max_length=255, title="Variable definition", description="A string containing a detailed description of the variable")
    speciation: str = Field(default=None, max_length=255, title="Speciation", description="A string containing the speciation for the variable from the ODM2 Speciation controllec vocabulary")


class TimeSeriesSite(BaseModel):
    """
    A class used to represent the metadata associated with a site contained within a time series aggregation
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    site_code: str = Field(max_length=200, title="Site code", description="A string containing a short but meaningful code identifying the site")
    site_name: str = Field(default=None, max_length=255, title="Site name", description="A string containing the name of the site")
    elevation_m: float = Field(default=None, title="Elevation", description="A floating point number expressing the elevation of the site in meters")
    elevation_datum: str = Field(default=None, max_length=50, title="Elevation datum", description="A string expressing the elevation datum used from the ODM2 Elevation Datum controlled vocabulary")
    site_type: str = Field(default=None, max_length=100, title="Site type", description="A string containing the type of site from the ODM2 Sampling Feature Type controlled vocabulary ")
    latitude: float = Field(default=None, title="Latitude", description="A floating point value expressing the latitude coordinate of the site")
    longitude: float = Field(default=None, title="Longitude", description="A floating point value expressing the longitude coordinate of the site")


class TimeSeriesMethod(BaseModel):
    """
    A class used to represent the metadata associated with a method contained within a time series aggregation
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    method_code: str = Field(max_length=50, title="Method code", description="A string containing a short but meaningful code identifying the method")
    method_name: str = Field(max_length=200, title="Method name", description="A string containing the name of the method")
    method_type: str = Field(max_length=200, title="Method type", description="A string containing the method type from the ODM2 Method Type controlled vocabulary")
    method_description: str = Field(default=None, title="Method description", description="A string containing a detailed description of the method")
    method_link: AnyUrl = Field(default=None, title="Method link", description="An object containg a URL that points to a website having a detailed description of the method")


class ProcessingLevel(BaseModel):
    """
    A class used to represent the metadata associated with a processing level contained within a time series aggregation
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    processing_level_code: str = Field(max_length=50, title="Processing level code", description="A string containing a short but meaningful code identifying the processing level")
    definition: str = Field(default=None, max_length=200, title="Definition", description="A string containing a description of the processing level")
    explanation: str = Field(default=None, title="Explanation", description="A string containing a more extensive explanation of the meaning of the processing level")


class Unit(BaseModel):
    """
    A class used to represent the metadata associated with a dimensional unit within a time series aggregation
    """

    class Config:
        title = 'TODO Jeff (title of class)'

    type: str = Field(max_length=255, title="Unit type", description="A string containing the type of unit from the ODM2 Units Type controlled vocabulary")
    name: str = Field(max_length=255, title="Unit name", description="A string containing the name of the unit from the ODM2 units list")
    abbreviation: str = Field(max_length=20, title="Unit abbreviation", description="A string containing an abbreviation for the unit from the ODM2 units list")


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
