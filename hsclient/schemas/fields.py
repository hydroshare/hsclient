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
        title = 'Related Resource Metadata'

    type: RelationType = Field(title="Relation type", description="The type of relationship with the related resource")
    value: str = Field(max_length=500, title="Value", description="String expressing the Full text citation, URL link for, or description of the related resource")

    _parse_relation = root_validator(pre=True)(parse_relation)


class CellInformation(BaseModel):
    """
    A class used to represent the metadata associated with raster grid cells in geographic raster aggregations
    """

    class Config:
        title = 'Raster Cell Metadata'

    # TODO: Is there such a thing as "name" for CellInformation?
    name: str = Field(default=None, max_length=500, title="Name", description="Name of the cell information")
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
        title = 'Rights Metadata'

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
        title = 'Creator Metadata'

    name: str = Field(default=None, max_length=100, title="Name", description="A string containing the name of the creator")
    phone: str = Field(default=None, max_length=25, title="Phone", description="A string containing a phone number for the creator")
    address: str = Field(default=None, max_length=250, title="Address", description="A string containing an address for the creator")
    organization: str = Field(default=None, max_length=200, title="Organization", description="A string containing the name of the organization with which the creator is affiliated")
    email: EmailStr = Field(default=None, title="Email", description="A string containing an email address for the creator")
    homepage: HttpUrl = Field(default=None, title="Homepage", description="An object containing the URL for website associated with the creator")
    # TODO: Is there such a thing as a "description" property for Creator?
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
    """

    class Config:
        title = 'Author Metadata'

    pass


class Contributor(BaseModel):
    """
    A class used to represent the metadata associated with a contributor to a resource
    """

    class Config:
        title = 'Contributor Metadata'

    name: str = Field(default=None, title="Name", description="A string containing the name of the contributor")
    phone: str = Field(default=None, title="Phone", description="A string containing a phone number for the contributor")
    address: str = Field(default=None, title="Address", description="A string containing an address for the contributor")
    organization: str = Field(default=None, title="Organization", description="A string containing the name of the organization with which the contributor is affiliated")
    email: EmailStr = Field(default=None, title="Email", description="A string containing an email address for the contributor")
    homepage: HttpUrl = Field(default=None, title="Homepage", description="An object containing the URL for website associated with the contributor")
    # TODO: is there such a thing as a "description" property for contributor?
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
        title = 'Funding Agency Metadata'

    funding_agency_name: str = Field(title="Agency name", description="A string containing the name of the funding agency or organization")
    title: str = Field(default=None, title="Award title", description="A string containing the title of the project or award")
    number: str = Field(default=None, title="Award number", description="A string containing the award number or other identifier")
    funding_agency_url: AnyUrl = Field(default=None, title="Agency URL", description="An object containing a URL pointing to a website describing the funding award")


class BandInformation(BaseModel):
    """
    A class used to represent the metadata associated with the raster bands of a geographic raster aggregation
    """

    class Config:
        title = 'Raster Band Metadata'

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
    A class used to represent the metadata associated with a field in the attribute table for a geographic
    feature aggregation
    """

    class Config:
        title = 'Geographic Feature Field Metadata'

    field_name: str = Field(max_length=128, title="Field name", description="A string containing the name of the attribute table field")
    field_type: str = Field(max_length=128, title="Field type", description="A string containing the data type of the values in the field")
    # TODO: What is the "field_type_code"? It's not displayed on the resource landing page, but it's encoded in the
    #  aggregation metadata as an integer value.
    field_type_code: str = Field(default=None, max_length=50, title="Field type code", description="A string value containing a code that indicates the field type")
    field_width: int = Field(default=None, title="Field width", description="An integer value containing the width of the attribute field")
    field_precision: int = Field(default=None, title="Field precision", description="An integer value containing the precision of the attribute field")


class GeometryInformation(BaseModel):
    """
    A class used to represent the metadata associated with the geometry of a geographic feature aggregation
    """

    class Config:
        title = 'Geographic Feature Geometry Metadata'

    feature_count: int = Field(default=0, title="Feature count", description="An integer containing the number of features in the geographic feature aggregation")
    geometry_type: str = Field(max_length=128, title="Geometry type", description="A string containing the type of features in the geographic feature aggregation")


class Variable(BaseModel):
    """
    A class used to represent the metadata associated with a variable contained within a multidimensional aggregation
    """

    class Config:
        title = 'Multidimensional Variable Metadata'

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
        title = 'Publisher Metadata'

    name: str = Field(max_length=200, title="Publisher name", description="A string containing the name of the publisher")
    url: AnyUrl = Field(title="Publisher URL", description="An object containing a URL that points to the publisher website")


class TimeSeriesVariable(BaseModel):
    """
    A class used to represent the metadata associated with a variable contained within a time series aggregation
    """

    class Config:
        title = 'Time Series Variable Metadata'

    variable_code: str = Field(max_length=50, title="Variable code", description="A string containing a short but meaningful code that identifies a variable")
    variable_name: str = Field(max_length=100, title="Variable name", description="A string containing the name of the variable")
    variable_type: str = Field(max_length=100, title="Variable type", description="A string containing the type of variable from the ODM2 VariableType controlled vocabulary")
    # TODO: The NoData value for a variable in an ODM2 database is not always an integer.
    #  It could be a floating point value. We might want to change this to a string or a floating point value
    no_data_value: int = Field(title="NoData value", description="The NoData value for the variable")
    variable_definition: str = Field(default=None, max_length=255, title="Variable definition", description="A string containing a detailed description of the variable")
    speciation: str = Field(default=None, max_length=255, title="Speciation", description="A string containing the speciation for the variable from the ODM2 Speciation controllec vocabulary")


class TimeSeriesSite(BaseModel):
    """
    A class used to represent the metadata associated with a site contained within a time series aggregation
    """

    class Config:
        title = 'Time Series Site Metadata'

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
        title = 'Time Series Method Metadata'

    method_code: str = Field(max_length=50, title="Method code", description="A string containing a short but meaningful code identifying the method")
    method_name: str = Field(max_length=200, title="Method name", description="A string containing the name of the method")
    method_type: str = Field(max_length=200, title="Method type", description="A string containing the method type from the ODM2 Method Type controlled vocabulary")
    method_description: str = Field(default=None, title="Method description", description="A string containing a detailed description of the method")
    method_link: AnyUrl = Field(default=None, title="Method link", description="An object containg a URL that points to a website having a detailed description of the method")


class ProcessingLevel(BaseModel):
    """
    A class used to represent the metadata associated with a processing level contained within a time series
    aggregation
    """

    class Config:
        title = 'Time Series Processing Level Metadata'

    processing_level_code: str = Field(max_length=50, title="Processing level code", description="A string containing a short but meaningful code identifying the processing level")
    definition: str = Field(default=None, max_length=200, title="Definition", description="A string containing a description of the processing level")
    explanation: str = Field(default=None, title="Explanation", description="A string containing a more extensive explanation of the meaning of the processing level")


class Unit(BaseModel):
    """
    A class used to represent the metadata associated with a dimensional unit within a time series aggregation
    """

    class Config:
        title = 'Time Series Units Metadata'

    type: str = Field(max_length=255, title="Unit type", description="A string containing the type of unit from the ODM2 Units Type controlled vocabulary")
    name: str = Field(max_length=255, title="Unit name", description="A string containing the name of the unit from the ODM2 units list")
    abbreviation: str = Field(max_length=20, title="Unit abbreviation", description="A string containing an abbreviation for the unit from the ODM2 units list")


class UTCOffSet(BaseModel):
    """
    A class used to represent the metadata associated with a UTC time offset within a time series aggregation)
    """

    class Config:
        title = 'Time Series UTC Offset Metadata'

    value: float = Field(default=0, title="UTC offset value", description="A floating point number containing the UTC time offset associated with the data values expressed in hours")


class TimeSeriesResult(BaseModel):
    """
    A class used to represent the metadata associated with a time series result within a time series aggregation
    """

    class Config:
        title = 'Time Series Result Metadata'

    series_id: str = Field(max_length=36, title="Series ID", description="A string containing a unique identifier for the time series result")
    unit: Unit = Field(default=None, title="Units", description="An object containing the units in which the values of the time series are expressed")
    status: str = Field(default=None, max_length=255, title="Status", description="A string containing the status of the time series result chosen from the ODM2 Status controlled vocabulary")
    sample_medium: str = Field(max_length=255, title="Sample medium", description="A string containing the sample medium in which the time series result was measured chosen from the ODM2 Medium controlled vocabulary")
    value_count: int = Field(title="Value count", description="An integer value containing the number of data values contained within the time series result")
    # TODO: "aggregation_statistic" should be singular
    aggregation_statistics: str = Field(max_length=255, title="Aggregation statistic", description="A string containing the aggregation statistic associated with the values of the time series result chosen from the ODM2 Aggregation Statistic controlled vocabulary")
    # TODO: Not sure what "series_label" is. It's not an ODM2 thing
    series_label: str = Field(default=None, max_length=255, title="Series label", description="A string containing a label for the time series result")
    site: TimeSeriesSite = Field(title="Site", description="An object containing metadata about the site at which the time series result was created")
    variable: TimeSeriesVariable = Field(title="Variablef", description="An object containing metadata about the observed variable associated with the time series result values")
    method: TimeSeriesMethod = Field(title="Method", description="An object containing metadata about the method used to produce the time series result values")
    processing_level: ProcessingLevel = Field(title="Processing level", description="An object containing metadata about the processing level or level of quality control to which the time series result values have been subjected")
    # TODO: Does "UTCOffset" really need to be an object given that it's just a floating point value?
    utc_offset: UTCOffSet = Field(default=None, title="UTC Offset", description="An object containing a floating point value that represents the time offset from UTC time in hours associated with the time series result value timestamps")


class BoxCoverage(base_models.BaseCoverage):
    """
    A class used to represent geographic coverage metadata for a resource or aggregation expressed as a
    latitude-longitude bounding box
    """

    class Config:
        title = 'Box Coverage Metadata'

    type: str = Field(default="box", const=True, title="Geographic coverage type", description="A string containing the type of geographic coverage")
    name: str = Field(default=None, title="Name", description="A string containing a name for the place associated with the geographic coverage")
    northlimit: float = Field(gt=-90, lt=90, title="North limit", description="A floating point value containing the constant coordinate for the northernmost face or edge of the bounding box")
    eastlimit: float = Field(gt=-180, lt=180, title="East limit", description="A floating point value containing the constant coordinate for the easternmost face or edge of the bounding box")
    southlimit: float = Field(gt=-90, lt=90, title="South limit", description="A floating point value containing the constant coordinate for the southernmost face or edge of the bounding box")
    westlimit: float = Field(gt=-180, lt=180, title="West limit", description="A floating point value containing the constant coordinate for the westernmost face or edge of the bounding box")
    units: str = Field(title="Units", description="A string containing the units applying to the unlabelled numeric values of northlimit, eastlimit, southlimit, and westlimit")
    projection: str = Field(default=None, title="Projection", description="A string containing the name of the projection used with any parameters required, such as ellipsoid parameters, datum, standard parallels and meridians, zone, etc.")

    @root_validator
    def compare_north_south(cls, values):
        north, south = values["northlimit"], values["southlimit"]
        if north < south:
            raise ValueError(f"North latitude [{north}] must be greater than or equal to South latitude [{south}]")
        return values


class BoxSpatialReference(base_models.BaseCoverage):
    """
    A class used to represent the metadata associated with the spatial reference of a geographic
    feature or raster aggregation expressed as a bounding box
    """

    class Config:
        title = 'Box Spatial Reference Metadata'

    type: str = Field(default="box", const=True, title="Spatial reference type", description="A string containing the type of spatial reference")
    name: str = Field(default=None, title="Name", description="A string containing a name for the place associated with the spatial reference")
    northlimit: float = Field(title="North limit", description="A floating point value containing the constant coordinate for the northernmost face or edge of the bounding box")
    eastlimit: float = Field(title="East limit", description="A floating point value containing the constant coordinate for the easternmost face or edge of the bounding box")
    southlimit: float = Field(title="South limit", description="A floating point value containing the constant coordinate for the southernmost face or edge of the bounding box")
    westlimit: float = Field(title="West limit", description="A floating point value containing the constant coordinate for the westernmost face or edge of the bounding box")
    units: str = Field(title="Units", description="A string containing the units applying to the unlabelled numeric values of northlimit, eastlimit, southlimit, and westlimit")
    # TODO: "projection" should probably be "projection_name"
    projection: str = Field(default=None, title="Projection", description="A string containing the name of the coordinate system used by the spatial reference")
    projection_string: str = Field(title="Projection string", description="A string containing an encoding of the coordinate system parameters")
    # TODO: I'm not sure what "projection_string_type" is - I don't see it in the RDF/XML encoding
    projection_string_type: str = Field(default=None, title="Projection string type", description="A string containing a description of the type of encoding for the projection string")
    datum: str = Field(default=None, title="Datum", description="A string containing the name of the datum used by the coordinate system")
    projection_name: str = Field(default=None, title="Projection name", description="A string containing the name of the coordinate system")


class MultidimensionalBoxSpatialReference(BoxSpatialReference):
    """
    A class used to represent the metadata associated with the spatial reference of a multidimensional
    aggregation expressed as a bounding box
    """

    class Config:
        title = 'Multidimensional Box Spatial Reference Metadata'


class PointCoverage(base_models.BaseCoverage):
    """
    A class used to represent geographic coverage metadata for a resource or aggregation expressed as a
    point location
    """

    class Config:
        title = 'Point Coverage Metadata'

    type: str = Field(default="point", const=True, title="Geographic coverage type", description="A string containing the type of geographic coverage")
    name: str = Field(default=None, title="Name", description="A string containing a name for the place associated with the geographic coverage")
    east: float = Field(gt=-180, lt=180, title="East", description="The coordinate of the point location measured in the east direction")
    north: float = Field(gt=-90, lt=90, title="North", description="The coordinate of the point location measured in the north direction")
    units: str = Field(title="Units", description="The units applying to the unlabelled numeric values of north and east")
    projection: str = Field(title="Projection", description="The name of the projection used with any parameters required, such as ellipsoid parameters, datum, standard parallels and meridians, zone, etc.")


class PointSpatialReference(base_models.BaseCoverage):
    """
    A class used to represent the metadata associated with the spatial reference of a geographic
    feature or raster aggregation expressed as a point
    """

    class Config:
        title = 'Point Spatial Reference Metadata'

    type: str = Field(default="point", const=True, title="Spatial reference type", description="A string containing the type of spatial reference")
    name: str = Field(default=None, title="Name", description="A string containing a name for the place associated with the spatial reference")
    east: float = Field(title="East", description="The coordinate of the point location measured in the east direction")
    north: float = Field(title="North", description="The coordinate of the point location measured in the north direction")
    units: str = Field(title="Units", description="The units applying to the unlabelled numeric values of north and east")
    projection: str = Field(title="Projection", description="A string containing the name of the coordinate system used by the spatial reference")
    projection_string: str = Field(title="Projection string", description="A string containing an encoding of the coordinate system parameters")
    # TODO: I'm not sure what "projection_string_type" is - I don't see it in the RDF/XML encoding
    projection_string_type: str = Field(default=None, title="Projection string type", description="A string containing a description of the type of encoding for the projection string")
    projection_name: str = Field(default=None, title="Projection name", description="A string containing the name of the coordinate system")


class MultidimensionalPointSpatialReference(PointSpatialReference):
    """
    A class used to represent the metadata associated with the spatial reference of a multidimensional
    aggregation expressed as a point
    """

    class Config:
        title = 'Multidimensional Point Spatial Reference Metadata'


class PeriodCoverage(base_models.BaseCoverage):
    """
    A class used to represent temporal coverage metadata for a resource or aggregation
    """

    class Config:
        title = 'Period Coverage Metadata'

    name: str = Field(default=None, title="Name", description="A string containing a name for the time interval")
    start: datetime = Field(title="Start", description="A datetime object containing the instant corresponding to the commencement of the time interval")
    end: datetime = Field(title="End", description="A datetime object containing the instant corresponding to the termination of the time interval")

    @root_validator
    def start_before_end(cls, values):
        start, end = values["start"], values["end"]
        if start > end:
            raise ValueError(f"start date [{start}] is after end date [{end}]")
        return values
