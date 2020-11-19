from datetime import datetime
from typing import List

from pydantic import AnyUrl, Field, HttpUrl, BaseModel, validator
from rdflib import Literal, URIRef

from hs_rdf.namespaces import RDF, RDFS, HSTERMS, DCTERMS
from hs_rdf.schemas.enums import CoverageType, DateType, VariableType
from hs_rdf.schemas.rdf_pydantic import RDFBaseModel


class DCType(RDFBaseModel):
    is_defined_by: AnyUrl = Field(rdf_predicate=RDFS.isDefinedBy)
    label: str = Field(rdf_predicate=RDFS.label)


class Source(RDFBaseModel):
    is_derived_from: str = Field(rdf_predicate=HSTERMS.isDerivedFrom, default=None)


class Relation(RDFBaseModel):
    is_copied_from: AnyUrl = Field(rdf_predicate=HSTERMS.isCopiedFrom, default=None)
    is_part_of: AnyUrl = Field(rdf_predicate=HSTERMS.isPartOf, default=None)


class Description(RDFBaseModel):
    abstract: str = Field(rdf_predicate=DCTERMS.abstract, default=None)


class Identifier(RDFBaseModel):
    hydroshare_identifier: AnyUrl = Field(rdf_predicate=HSTERMS.hydroShareIdentifier)


class ExtendedMetadata(RDFBaseModel):
    value: str = Field(rdf_predicate=HSTERMS.value)
    key: str = Field(rdf_predicate=HSTERMS.key)


class CellInformation(RDFBaseModel):
    name: str = Field(rdf_predicate=HSTERMS.name)
    rows: int = Field(rdf_predicate=HSTERMS.rows)
    columns: int = Field(rdf_predicate=HSTERMS.columns)
    cell_size_x_value: float = Field(rdf_predicate=HSTERMS.cellSizeXValue)
    cell_data_type: str = Field(rdf_predicate=HSTERMS.cellDataType)
    cell_size_y_value: float = Field(rdf_predicate=HSTERMS.cellSizeYValue)


class Date(RDFBaseModel):
    type: DateType = Field(rdf_predicate=RDF.type)
    value: datetime = Field(rdf_predicate=RDF.value)


class Rights(RDFBaseModel):
    rights_statement: str = Field(rdf_predicate=HSTERMS.rightsStatement)
    url: AnyUrl = Field(rdf_predicate=HSTERMS.URL)


class Creator(RDFBaseModel):
    creator_order: int = Field(rdf_predicate=HSTERMS.creatorOrder)
    name: str = Field(rdf_predicate=HSTERMS.name)

    email: str = Field(rdf_predicate=HSTERMS.email, default=None)
    organization: str = Field(rdf_predicate=HSTERMS.organization, default=None)


class Contributor(RDFBaseModel):
    name: str = Field(rdf_predicate=HSTERMS.name, default=None)
    google_scholar_id: AnyUrl = Field(rdf_predicate=HSTERMS.GoogleScholarID, default=None)
    research_gate_id: AnyUrl = Field(rdf_predicate=HSTERMS.ResearchGateID, default=None)
    phone: str = Field(rdf_predicate=HSTERMS.phone, default=None)
    ORCID: AnyUrl = Field(rdf_predicate=HSTERMS.ORCID, default=None)
    address: str = Field(rdf_predicate=HSTERMS.address, default=None)
    organization: str = Field(rdf_predicate=HSTERMS.organization, default=None)
    email: str = Field(rdf_predicate=HSTERMS.email, default=None)
    homepage: HttpUrl = Field(rdf_predicate=HSTERMS.homepage, default=None)


class AwardInfo(RDFBaseModel):
    funding_agency_name: str = Field(rdf_predicate=HSTERMS.fundingAgencyName, default=None)
    award_title: str = Field(rdf_predicate=HSTERMS.awardTitle, default=None)
    award_number: str = Field(rdf_predicate=HSTERMS.awardNumber, default=None)
    funding_agency_url: HttpUrl = Field(rdf_predicate=HSTERMS.fundingAgencyURL, default=None)


class BandInformation(RDFBaseModel):
    name: str = Field(rdf_predicate=HSTERMS.name)
    variable_name: str = Field(rdf_predicate=HSTERMS.variableName, default=None)
    variable_unit: str = Field(rdf_predicate=HSTERMS.variableUnit, default=None)

    no_data_value: str = Field(rdf_predicate=HSTERMS.noDataValue, default=None)
    maximum_value: List[str] = Field(rdf_predicate=HSTERMS.maximumValue, default=None)
    comment: str = Field(rdf_predicate=HSTERMS.comment, default=None)
    method: str = Field(rdf_predicate=HSTERMS.method, default=None)
    minimum_value: List[str] = Field(rdf_predicate=HSTERMS.minimumValue, default=None)


class BaseCoverage(BaseModel):
    type: CoverageType

    def __str__(self):
        return "; ".join(["=".join([key, val.isoformat() if isinstance(val, datetime) else str(val)])
                          for key, val in self.__dict__.items()
                          if key != "type" and val])


class BoxCoverage(BaseCoverage):
    type: CoverageType = Field(default=CoverageType.box, const=True)
    name: str = None
    northlimit: float
    eastlimit: float
    southlimit: float
    westlimit: float
    units: str
    projection: str


class PointCoverage(BaseCoverage):
    type: CoverageType = Field(default=CoverageType.point, const=True)
    name: str = None
    east: float
    north: float
    units: str
    projection: str


class PeriodCoverage(BaseCoverage):
    type: CoverageType = Field(default=CoverageType.period, const=True)
    start: datetime
    end: datetime
    scheme: str = None


class Coverage(RDFBaseModel):
    type: CoverageType = Field(rdf_predicate=RDF.type)
    value: BaseCoverage = Field(rdf_predicate=RDF.value)

    @validator('value', pre=True)
    def convert_str_to_coverage(cls, v, values, **kwargs):
        if isinstance(v, str):
            if 'type' in values:
                cov_type = CoverageType(values['type'])
                cov_kwargs = {}
                for key_value in v.split("; "):
                    k, v = key_value.split("=")
                    cov_kwargs[k] = v

                if cov_type == CoverageType.box:
                    return BoxCoverage(**cov_kwargs)
                if cov_type == CoverageType.point:
                    return PointCoverage(**cov_kwargs)
                if cov_type == CoverageType.period:
                    return PeriodCoverage(**cov_kwargs)
        return v


class BaseSpatialReference(BaseModel):
    type: CoverageType = None

    def __str__(self):
        return "; ".join(["=".join([key, val.isoformat() if isinstance(val, datetime) else str(val)])
                          for key, val in self.__dict__.items()
                          if key != "type" and val])


class PointSpatialReference(BaseSpatialReference):
    name: str = None
    east: float
    north: float
    units: str
    projection: str = None
    projection_name: str = None
    projection_string: str
    datum: str
    projection_string_type: str = None


class BoxSpatialReference(BaseSpatialReference):
    northlimit: float
    southlimit: float
    westlimit: float
    eastlimit: float
    projection_name: str = None
    projection_string: str
    units: str
    datum: str
    name: str = None
    projection: str = None
    projection_string_type: str = None


class SpatialReference(RDFBaseModel):
    type: CoverageType = Field(rdf_predicate=RDF.type)
    value: BaseSpatialReference = Field(rdf_predicate=RDF.value)

    @validator('value', pre=True)
    def convert_str_to_spatial_coverage(cls, v, values, **kwargs):
        if isinstance(v, str):
            if 'type' in values:
                cov_type = CoverageType(values['type'])
                cov_kwargs = {}
                for key_value in v.split("; "):
                    k, v = key_value.split("=")
                    cov_kwargs[k] = v

                # TODO, hydroshare is inconsistent serving these types
                if cov_type == CoverageType.box or cov_type == CoverageType.spatial_box:
                    bsr = BoxSpatialReference(**cov_kwargs)
                    bsr.type = cov_type
                    return bsr
                if cov_type == CoverageType.spatial_point or cov_type == CoverageType.point:
                    psr = PointSpatialReference(**cov_kwargs)
                    psr.type = cov_type
                    return psr
        return v



class FieldInformation(RDFBaseModel):
    fieldname: str = Field(rdf_predicate=HSTERMS.fieldName, default=None)
    fieldtype: str = Field(rdf_predicate=HSTERMS.fieldType, default=None)
    fieldTypeCode: str = Field(rdf_predicate=HSTERMS.fieldTypeCode, default=None)
    fieldWidth: int = Field(rdf_predicate=HSTERMS.fieldWidth, default=None)
    fieldPrecision: int = Field(rdf_predicate=HSTERMS.fieldPrecision, default=None)


class GeometryInformation(RDFBaseModel):
    featureCount: int = Field(rdf_predicate=HSTERMS.featureCount, default=None)
    geometryType: str = Field(rdf_predicate=HSTERMS.geometryType, default=None)

class Variable(RDFBaseModel):
    name: str = Field(rdf_predicate=HSTERMS.name)
    unit: str = Field(rdf_predicate=HSTERMS.unit)
    type: VariableType = Field(rdf_predicate=HSTERMS.type)
    shape: str = Field(rdf_predicate=HSTERMS.shape)
    descriptive_name: str = Field(rdf_predicate=HSTERMS.descriptive_name, default=None)
    method: str = Field(rdf_predicate=HSTERMS.method, default=None)
    missing_value: str = Field(rdf_predicate=HSTERMS.missing_value, default=None)

class Publisher(RDFBaseModel):
    name: str = Field(rdf_predicate=HSTERMS.publisherName)
    url: AnyUrl = Field(rdf_predicate=HSTERMS.publisherURL)

class Format(RDFBaseModel):
    value: str = Field(rdf_predicate=HSTERMS.value)
