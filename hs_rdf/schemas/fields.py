from datetime import datetime
from typing import List
from enum import Enum

from pydantic import AnyUrl, Field, HttpUrl
from rdflib import Literal, URIRef

from hs_rdf.namespaces import RDF, DC, RDFS, HSTERMS, DCTERMS
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
    abstract: str = Field(rdf_predicate=DCTERMS.abstract)


class Coverage(RDFBaseModel):
    value: str = Field(rdf_predicate=RDF.value)
    type: AnyUrl = Field(rdf_predicate=RDF.type)


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


class DateType(Enum):
    modified = str(DCTERMS.modified)
    created = str(DCTERMS.created)
    valid = str(DCTERMS.valid)
    available = str(DCTERMS.available)
    published = str(DCTERMS.published)


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


class SpatialReference(RDFBaseModel):
    northlimit: float = None
    southlimit: float = None
    westlimit: float = None
    eastlimit: float = None
    projection: str = None
    projection_string: str = None
    projection_string_type: str = None
    projection_name: str = None
    datum: str = None
    unit: str = None

    type: AnyUrl = Field(rdf_predicate=RDF.type, default=None)

    def rdf(self, graph):
        value_dict = {}
        if self.northlimit:
            value_dict['northlimit'] = self.northlimit
        if self.southlimit:
            value_dict['southlimit'] = self.southlimit
        if self.eastlimit:
            value_dict['eastlimit'] = self.eastlimit
        if self.westlimit:
            value_dict['westlimit'] = self.westlimit
        if self.projection:
            value_dict['projection'] = self.projection
        if self.unit:
            value_dict['units'] = self.unit
        if self.projection_string:
            value_dict['projection_string'] = self.projection_string
        if self.projection_name:
            value_dict['projection_name'] = self.projection_name
        if self.projection_string_type:
            value_dict['projection_string_type'] = self.projection_string_type
        if self.datum:
            value_dict['datum'] = self.datum

        value_string = "; ".join(["=".join([key, str(val)]) for key, val in value_dict.items()])

        graph.add((self.rdf_subject, RDF.type, URIRef(self.type)))
        graph.add((self.rdf_subject, RDF.value, Literal(value_string)))
        return graph

    @classmethod
    def parse(cls, metadata_graph, subject=None):
        if not subject:
            raise Exception("subject is required for parsing SpatialReference")

        rdf_type = metadata_graph.value(subject=subject, predicate=RDF.type)
        value = metadata_graph.value(subject=subject, predicate=RDF.value)
        value_dict = {"type": rdf_type}
        if value:
            for key_value in value.split("; "):
                k, v = key_value.split("=")
                if k == 'units':
                    value_dict['unit'] = v
                else:
                    value_dict[k] = v
            return SpatialReference(**value_dict)


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
    name: str = Field(rdf_predicate=HSTERMS.name, default=None)
    unit: str = Field(rdf_predicate=HSTERMS.unit, default=None)
    type: str = Field(rdf_predicate=HSTERMS.type, default=None)
    shape: str = Field(rdf_predicate=HSTERMS.shape, default=None)
    descriptive_name: str = Field(rdf_predicate=HSTERMS.descriptive_name, default=None)
    method: str = Field(rdf_predicate=HSTERMS.method, default=None)
    missing_value: str = Field(rdf_predicate=HSTERMS.missing_value, default=None)

class Publisher(RDFBaseModel):
    name: str = Field(rdf_predicate=HSTERMS.publisherName, default=None)
    url: AnyUrl = Field(rdf_predicate=HSTERMS.publisherURL, default=None)

class Format(RDFBaseModel):
    value: str = Field(rdf_predicate=HSTERMS.value, default=None)
