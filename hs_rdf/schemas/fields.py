from datetime import datetime
from typing import List

from pydantic import AnyUrl, Field, HttpUrl, BaseModel, validator
from rdflib import Literal, URIRef

from hs_rdf.namespaces import RDF, RDFS, HSTERMS, DCTERMS
from hs_rdf.schemas.enums import CoverageType, DateType, VariableType, SpatialReferenceType
from hs_rdf.schemas.rdf_pydantic import RDFBaseModel


class DCType(RDFBaseModel):
    is_defined_by: AnyUrl = Field(rdf_predicate=RDFS.isDefinedBy)
    label: str = Field(rdf_predicate=RDFS.label)


class SourceInRDF(RDFBaseModel):
    is_derived_from: str = Field(rdf_predicate=HSTERMS.isDerivedFrom, default=None)


class RelationInRDF(RDFBaseModel):
    is_copied_from: AnyUrl = Field(rdf_predicate=HSTERMS.isCopiedFrom, default=None)
    is_part_of: AnyUrl = Field(rdf_predicate=HSTERMS.isPartOf, default=None)


class DescriptionInRDF(RDFBaseModel):
    abstract: str = Field(rdf_predicate=DCTERMS.abstract, default=None)


class IdentifierInRDF(RDFBaseModel):
    hydroshare_identifier: AnyUrl = Field(rdf_predicate=HSTERMS.hydroShareIdentifier)


class ExtendedMetadataInRDF(RDFBaseModel):
    value: str = Field(rdf_predicate=HSTERMS.value)
    key: str = Field(rdf_predicate=HSTERMS.key)


class CellInformation(RDFBaseModel):
    name: str = Field(rdf_predicate=HSTERMS.name)
    rows: int = Field(rdf_predicate=HSTERMS.rows)
    columns: int = Field(rdf_predicate=HSTERMS.columns)
    cell_size_x_value: float = Field(rdf_predicate=HSTERMS.cellSizeXValue)
    cell_data_type: str = Field(rdf_predicate=HSTERMS.cellDataType)
    cell_size_y_value: float = Field(rdf_predicate=HSTERMS.cellSizeYValue)


class DateInRDF(RDFBaseModel):
    type: DateType = Field(rdf_predicate=RDF.type)
    value: datetime = Field(rdf_predicate=RDF.value)


class RightsInRDF(RDFBaseModel):
    rights_statement: str = Field(rdf_predicate=HSTERMS.rightsStatement)
    url: AnyUrl = Field(rdf_predicate=HSTERMS.URL)


class CreatorInRDF(RDFBaseModel):
    creator_order: int = Field(rdf_predicate=HSTERMS.creatorOrder)
    name: str = Field(rdf_predicate=HSTERMS.name)

    email: str = Field(rdf_predicate=HSTERMS.email, default=None)
    organization: str = Field(rdf_predicate=HSTERMS.organization, default=None)


class ContributorInRDF(RDFBaseModel):
    name: str = Field(rdf_predicate=HSTERMS.name, default=None)
    google_scholar_id: AnyUrl = Field(rdf_predicate=HSTERMS.GoogleScholarID, default=None)
    research_gate_id: AnyUrl = Field(rdf_predicate=HSTERMS.ResearchGateID, default=None)
    phone: str = Field(rdf_predicate=HSTERMS.phone, default=None)
    ORCID: AnyUrl = Field(rdf_predicate=HSTERMS.ORCID, default=None)
    address: str = Field(rdf_predicate=HSTERMS.address, default=None)
    organization: str = Field(rdf_predicate=HSTERMS.organization, default=None)
    email: str = Field(rdf_predicate=HSTERMS.email, default=None)
    homepage: HttpUrl = Field(rdf_predicate=HSTERMS.homepage, default=None)


class AwardInfoInRDF(RDFBaseModel):
    funding_agency_name: str = Field(rdf_predicate=HSTERMS.fundingAgencyName, default=None)
    award_title: str = Field(rdf_predicate=HSTERMS.awardTitle, default=None)
    award_number: str = Field(rdf_predicate=HSTERMS.awardNumber, default=None)
    funding_agency_url: HttpUrl = Field(rdf_predicate=HSTERMS.fundingAgencyURL, default=None)


class BandInformation(RDFBaseModel):
    name: str = Field(rdf_predicate=HSTERMS.name)
    variable_name: str = Field(rdf_predicate=HSTERMS.variableName, default=None)
    variable_unit: str = Field(rdf_predicate=HSTERMS.variableUnit, default=None)

    no_data_value: str = Field(rdf_predicate=HSTERMS.noDataValue, default=None)
    maximum_value: str = Field(rdf_predicate=HSTERMS.maximumValue, default=None)
    comment: str = Field(rdf_predicate=HSTERMS.comment, default=None)
    method: str = Field(rdf_predicate=HSTERMS.method, default=None)
    minimum_value: str = Field(rdf_predicate=HSTERMS.minimumValue, default=None)


class CoverageInRDF(RDFBaseModel):
    type: CoverageType = Field(rdf_predicate=RDF.type)
    value: str = Field(rdf_predicate=RDF.value)


class SpatialReferenceInRDF(RDFBaseModel):
    type: SpatialReferenceType = Field(rdf_predicate=RDF.type)
    value: str = Field(rdf_predicate=RDF.value)


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

class PublisherInRDF(RDFBaseModel):
    name: str = Field(rdf_predicate=HSTERMS.publisherName)
    url: AnyUrl = Field(rdf_predicate=HSTERMS.publisherURL)

class FormatInRDF(RDFBaseModel):
    value: str = Field(rdf_predicate=HSTERMS.value)
