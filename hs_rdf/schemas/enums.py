from enum import Enum

from hs_rdf.namespaces import DCTERMS


class AnyUrlEnum(str, Enum):
    pass

class CoverageType(AnyUrlEnum):
    period = str(DCTERMS.period)
    box = str(DCTERMS.box)
    point = str(DCTERMS.point)


class DateType(AnyUrlEnum):
    modified = str(DCTERMS.modified)
    created = str(DCTERMS.created)
    valid = str(DCTERMS.valid)
    available = str(DCTERMS.available)
    published = str(DCTERMS.published)


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