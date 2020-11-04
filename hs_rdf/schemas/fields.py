from datetime import datetime
from typing import List

from pydantic import AnyUrl, Field, HttpUrl

from hs_rdf.namespaces import RDF, DC, RDFS, HSTERMS, DCTERMS
from hs_rdf.schemas.rdf_pydantic import RDFBaseModel


class DCType(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=DC.type)

    is_defined_by: AnyUrl = Field(rdf_predicate=RDFS.isDefinedBy)
    label: str = Field(rdf_predicate=RDFS.label)


class Source(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=DC.source)

    is_derived_from: str = Field(rdf_predicate=HSTERMS.isDerivedFrom, default=None)


class Relation(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=DC.relation)

    is_copied_from: str = Field(rdf_predicate=HSTERMS.isCopiedFrom, default=None)
    is_part_of: str = Field(rdf_predicate=HSTERMS.isPartOf, default=None)


class Description(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=DC.Description)

    abstract: str = Field(rdf_predicate=DCTERMS.abstract)


class Coverage(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=DC.coverage)

    value: str = Field(rdf_predicate=RDF.value)
    type: str = Field(rdf_predicate=RDF.type)


class Identifier(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=DC.identifier)

    hydroshare_identifier: AnyUrl = Field(rdf_predicate=HSTERMS.hydroShareIdentifier)


class ExtendedMetadata(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.extendedMetadata)

    value: str = Field(rdf_predicate=HSTERMS.value)
    key: str = Field(rdf_predicate=HSTERMS.key)


class CellInformation(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.CellInformation)

    name: str = Field(rdf_predicate=HSTERMS.name)
    rows: str = Field(rdf_predicate=HSTERMS.rows)
    columns: str = Field(rdf_predicate=HSTERMS.columns)
    cell_size_x_value: str = Field(rdf_predicate=HSTERMS.cellSizeXValue)
    cell_data_type: str = Field(rdf_predicate=HSTERMS.cellDataType)
    cell_size_y_value: str = Field(rdf_predicate=HSTERMS.cellSizeYValue)


class Date(RDFBaseModel):
    type: AnyUrl = Field(rdf_predicate=RDF.type)
    value: datetime = Field(rdf_predicate=RDF.value)


class Rights(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=DC.rights)

    rights_statement: str = Field(rdf_predicate=HSTERMS.rightsStatement)
    url: AnyUrl = Field(rdf_predicate=HSTERMS.URL)


class Creator(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=DC.creator)

    creator_order: int = Field(rdf_predicate=HSTERMS.creatorOrder)
    name: str = Field(rdf_predicate=HSTERMS.name)

    email: str = Field(rdf_predicate=HSTERMS.email, default=None)
    organization: str = Field(rdf_predicate=HSTERMS.organization, default=None)


class Contributor(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=DC.contributor, include=False)

    google_scholar_id: str = Field(rdf_predicate=HSTERMS.GoogleScholarID, default=None)
    research_gate_id: str = Field(rdf_predicate=HSTERMS.ResearchGateID, default=None)
    phone: str = Field(rdf_predicate=HSTERMS.phone, default=None)
    ORCID: str = Field(rdf_predicate=HSTERMS.ORCID, default=None)
    address: str = Field(rdf_predicate=HSTERMS.address, default=None)
    organization: str = Field(rdf_predicate=HSTERMS.organization, default=None)
    email: str = Field(rdf_predicate=HSTERMS.email, default=None)
    homepage: HttpUrl = Field(rdf_predicate=HSTERMS.homepage, default=None)


class AwardInfo(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.awardInfo)

    funding_agency_name: str = Field(rdf_predicate=HSTERMS.fundingAgencyName, default=None)
    award_title: str = Field(rdf_predicate=HSTERMS.awardTitle, default=None)
    award_number: str = Field(rdf_predicate=HSTERMS.awardNumber, default=None)
    funding_agency_url: HttpUrl = Field(rdf_predicate=HSTERMS.fundingAgencyURL, default=None)


class BandInformation(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.BandInformation)

    name: str = Field(rdf_predicate=HSTERMS.name)
    variable_name: str = Field(rdf_predicate=HSTERMS.variableName)
    variable_unit: str = Field(rdf_predicate=HSTERMS.variableUnit)

    no_data_value: str = Field(rdf_predicate=HSTERMS.noDataValue, default=None)
    maximum_value: List[str] = Field(rdf_predicate=HSTERMS.maximumValue, default=None)
    comment: str = Field(rdf_predicate=HSTERMS.comment, default=None)
    method: str = Field(rdf_predicate=HSTERMS.method, default=None)
    minimum_value: List[str] = Field(rdf_predicate=HSTERMS.minimumValue, default=None)


class SpatialReference(RDFBaseModel):
    rdf_type: AnyUrl = Field(rdf_predicate=RDF.type, const=True, default=HSTERMS.spatialReference)

    # TODO fix these fields
    value: str = Field(rdf_predicate=RDF.value, default=None)
    type: str = Field(rdf_predicate=RDF.type, default=None)
