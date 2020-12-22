from enum import Enum

from hs_rdf.namespaces import DCTERMS, HSTERMS


class StringEnum(str, Enum):
    pass

class CoverageType(StringEnum):
    period = str(DCTERMS.period)
    box = str(DCTERMS.box)
    point = str(DCTERMS.point)


class SpatialReferenceType(StringEnum):
    point = str(HSTERMS.point)
    box = str(HSTERMS.box)


class MultidimensionalSpatialReferenceType(StringEnum):
    point = str(DCTERMS.point)
    box = str(DCTERMS.box)


class VariableType(Enum):
    Char = 'Char'  # 8-bit byte that contains uninterpreted character data
    Byte = 'Byte'  # integer(8bit)
    Short = 'Short'  # signed integer (16bit)
    Int = 'Int'  # signed integer (32bit)
    Float = 'Float'  # floating point (32bit)
    Double = 'Double'  # floating point(64bit)
    Int64 = 'Int64'  # integer(64bit)
    Unsigned_Byte = 'Unsigned Byte'
    Unsigned_Short = 'Unsigned Short'
    Unsigned_Int = 'Unsigned Int'
    Unsigned_Int64 = 'Unsigned Int64'
    String = 'String'  # variable length character string
    User_Defined_Type = 'User Defined Type'  # compound, vlen, opaque, enum
    Unknown = 'Unknown'


class UserIdentifierType(Enum):
    google_scholar_id = "GoogleScholarID"
    research_gate_id = "ResearchGateID"
    ORCID = "ORCID"


class RelationType(Enum):
    isCopiedFrom = 'The content of this resource was copied from'
    isPartOf = 'The content of this resource is part of'
    hasPart = 'Has Part'
    isExecutedBy = 'The content of this resource can be executed by'
    isCreatedBy = 'The content of this resource was created by'
    isVersionOf = 'Version Of'
    isReplacedBy = 'Replaced By'
    isDataFor = 'The content of this resource serves as the data for'
    cites = 'This resource cites'
    isDescribedBy = 'This resource is described by'


class AggregationType(Enum):

    SingleFileAggregation = "Generic"
    FileSetAggregation = "FileSet"
    GeographicRasterAggregation = "GeoRaster"
    MultidimensionalAggregation = "NetCDF"
    GeographicFeatureAggregation = "GeoFeature"
    ReferencedTimeSeriesAggregation = "RefTimeseries"
    TimeSeriesAggregation = "TimeSeries"


class DateType(StringEnum):
    modified = str(DCTERMS.modified)
    created = str(DCTERMS.created)
    valid = str(DCTERMS.valid)
    available = str(DCTERMS.available)
    published = str(DCTERMS.published)