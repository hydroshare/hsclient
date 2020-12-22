from datetime import datetime
from typing import Dict

from pydantic import AnyUrl, Field, HttpUrl, BaseModel, PositiveInt, validator, root_validator, EmailStr
from rdflib import BNode
from rdflib.term import Identifier as RDFIdentifier

from hs_rdf.namespaces import RDF, RDFS, HSTERMS, DCTERMS
from hs_rdf.schemas.data_structures import User
from hs_rdf.schemas.enums import CoverageType, DateType, VariableType, SpatialReferenceType, \
    MultidimensionalSpatialReferenceType, RelationType, UserIdentifierType
from hs_rdf.schemas.root_validators import parse_relation, parse_relation_rdf, group_user_identifiers, \
    split_user_identifiers
from hs_rdf.schemas.validators import validate_user_url


class RDFBaseModel(BaseModel):
    rdf_subject: RDFIdentifier = Field(default_factory=BNode)


class DCTypeInRDF(RDFBaseModel):
    is_defined_by: AnyUrl = Field(rdf_predicate=RDFS.isDefinedBy)
    label: str = Field(rdf_predicate=RDFS.label)


class SourceInRDF(RDFBaseModel):
    is_derived_from: str = Field(rdf_predicate=HSTERMS.isDerivedFrom, default=None)


class Relation(BaseModel):
    type: RelationType
    value: str = Field(max_length=500)

    _parse_relation = root_validator(pre=True)(parse_relation)


class RelationInRDF(RDFBaseModel):
    isHostedBy: str = Field(rdf_predicate=HSTERMS.isHostedBy, default=None)
    isCopiedFrom: str = Field(rdf_predicate=HSTERMS.isCopiedFrom, default=None)
    isPartOf: str = Field(rdf_predicate=HSTERMS.isPartOf, default=None)
    hasPart: str = Field(rdf_predicate=HSTERMS.hasPart, default=None)
    isExecutedBy: str = Field(rdf_predicate=HSTERMS.isExecutedBy, default=None)
    isCreatedBy: str = Field(rdf_predicate=HSTERMS.isCreatedBy, default=None)
    isVersionOf: str = Field(rdf_predicate=HSTERMS.isVersionOf, default=None)
    isReplacedBy: str = Field(rdf_predicate=HSTERMS.isReplacedBy, default=None)
    isDataFor: str = Field(rdf_predicate=HSTERMS.isDataFor, default=None)
    cites: str = Field(rdf_predicate=HSTERMS.cites, default=None)
    isDescribedBy: str = Field(rdf_predicate=HSTERMS.isDescribedBy, default=None)

    _parse_relation = root_validator(pre=True)(parse_relation_rdf)


class DescriptionInRDF(RDFBaseModel):
    abstract: str = Field(rdf_predicate=DCTERMS.abstract, default=None)


class IdentifierInRDF(RDFBaseModel):
    hydroshare_identifier: AnyUrl = Field(rdf_predicate=HSTERMS.hydroShareIdentifier)


class ExtendedMetadataInRDF(RDFBaseModel):
    value: str = Field(rdf_predicate=HSTERMS.value)
    key: str = Field(rdf_predicate=HSTERMS.key)


class CellInformation(BaseModel):
    name: str = Field(default=None, max_length=500)
    rows: int = Field(default=None)
    columns: int = Field(default=None)
    cell_size_x_value: float = Field(default=None)
    cell_data_type: str = Field(default=None, max_length=50)
    cell_size_y_value: float = Field(default=None)


class CellInformationInRDF(CellInformation, RDFBaseModel):

    class Config:
        fields = {'name': {"rdf_predicate": HSTERMS.name},
                  'rows': {"rdf_predicate": HSTERMS.rows},
                  'columns': {"rdf_predicate": HSTERMS.columns},
                  'cell_size_x_value': {"rdf_predicate": HSTERMS.cellSizeXValue},
                  'cell_data_type': {"rdf_predicate": HSTERMS.cellDataType},
                  'cell_size_y_value': {"rdf_predicate": HSTERMS.cellSizeYValue}}


class DateInRDF(RDFBaseModel):
    type: DateType = Field(rdf_predicate=RDF.type)
    value: datetime = Field(rdf_predicate=RDF.value)


class Rights(BaseModel):
    statement: str = Field()
    url: AnyUrl = Field()

    @classmethod
    def Creative_Commons_Attribution_CC_BY(cls):
        return Rights(statement="This resource is shared under the Creative Commons Attribution CC BY.",
                      url="http://creativecommons.org/licenses/by/4.0/")

    @classmethod
    def Creative_Commons_Attribution_ShareAlike_CC_BY(cls):
        return Rights(statement="This resource is shared under the Creative Commons Attribution-ShareAlike CC BY-SA.",
                      url="http://creativecommons.org/licenses/by-sa/4.0/")

    @classmethod
    def Creative_Commons_Attribution_NoDerivs_CC_BY_ND(cls):
        return Rights(statement="This resource is shared under the Creative Commons Attribution-ShareAlike CC BY-SA.",
                      url="http://creativecommons.org/licenses/by-nd/4.0/")

    @classmethod
    def Creative_Commons_Attribution_NoCommercial_ShareAlike_CC_BY_NC_SA(cls):
        return Rights(statement="This resource is shared under the Creative Commons Attribution-NoCommercial-ShareAlike"
                                " CC BY-NC-SA.",
                      url="http://creativecommons.org/licenses/by-nc-sa/4.0/")

    @classmethod
    def Creative_Commons_Attribution_NoCommercial_CC_BY_NC(cls):
        return Rights(statement="This resource is shared under the Creative Commons Attribution-NoCommercial CC BY-NC.",
                      url="http://creativecommons.org/licenses/by-nc/4.0/")

    @classmethod
    def Creative_Commons_Attribution_NoCommercial_NoDerivs_CC_BY_NC_ND(cls):
        return Rights(statement="This resource is shared under the Creative Commons Attribution-NoCommercial-NoDerivs "
                                "CC BY-NC-ND.",
                      url="http://creativecommons.org/licenses/by-nc-nd/4.0/")

    @classmethod
    def Other(cls, statement, url):
        return Rights(statement=statement, url=url)


class RightsInRDF(Rights, RDFBaseModel):

    class Config:
        fields = {'statement': {"rdf_predicate": HSTERMS.rightsStatement},
                  'url': {"rdf_predicate": HSTERMS.URL}}


class Creator(BaseModel):
    name: str = Field(default=None, max_length=100)

    phone: str = Field(default=None, max_length=25)
    address: str = Field(default=None, max_length=250)
    organization: str = Field(default=None, max_length=200)
    email: EmailStr = Field(default=None)
    homepage: HttpUrl = Field(default=None)
    description: str = Field(max_length=50, default=None)
    identifiers: Dict[UserIdentifierType, AnyUrl] = Field(default={})

    _description_validator = validator("description", pre=True)(validate_user_url)

    _split_identifiers = root_validator(pre=True, allow_reuse=True)(group_user_identifiers)

    @classmethod
    def from_user(cls, user: User):
        user_dict = user.dict()
        user_dict["description"] = user.url.path
        if user.website:
            user_dict["homepage"] = user.website

        return Creator(**user_dict)


class CreatorInRDF(RDFBaseModel):
    creator_order: PositiveInt
    name: str = Field(default=None)
    phone: str = Field(default=None)
    address: str = Field(default=None)
    organization: str = Field(default=None)
    email: EmailStr = Field(default=None)
    homepage: HttpUrl = Field(default=None)
    description: str = Field(max_length=50, default=None)
    ORCID: AnyUrl = Field(default=None)
    google_scholar_id: AnyUrl = Field(default=None)
    research_gate_id: AnyUrl = Field(default=None)

    _group_identifiers = root_validator(pre=True, allow_reuse=True)(split_user_identifiers)

    class Config:
        fields = {'name': {"rdf_predicate": HSTERMS.name},
                  'creator_order': {"rdf_predicate": HSTERMS.creatorOrder},
                  'google_scholar_id': {"rdf_predicate": HSTERMS.GoogleScholarID},
                  'research_gate_id': {"rdf_predicate": HSTERMS.ResearchGateID},
                  'phone': {"rdf_predicate": HSTERMS.phone},
                  'ORCID': {"rdf_predicate": HSTERMS.ORCID},
                  'address': {"rdf_predicate": HSTERMS.address},
                  'organization': {"rdf_predicate": HSTERMS.organization},
                  'email': {"rdf_predicate": HSTERMS.email},
                  'homepage': {"rdf_predicate": HSTERMS.homepage},
                  'description': {"rdf_predicate": HSTERMS.description}}


class Contributor(BaseModel):
    name: str = Field(default=None)
    phone: str = Field(default=None)
    address: str = Field(default=None)
    organization: str = Field(default=None)
    email: EmailStr = Field(default=None)
    homepage: HttpUrl = Field(default=None)
    identifiers: Dict[UserIdentifierType, AnyUrl] = Field(default={})

    _split_identifiers = root_validator(pre=True, allow_reuse=True)(group_user_identifiers)

    @classmethod
    def from_user(cls, user: User):
        user_dict = user.dict()
        user_dict["description"] = user.url.path
        if user.website:
            user_dict["homepage"] = user.website

        return Contributor(**user_dict)


class ContributorInRDF(RDFBaseModel):
    name: str = Field(default=None)
    phone: str = Field(default=None)
    address: str = Field(default=None)
    organization: str = Field(default=None)
    email: EmailStr = Field(default=None)
    homepage: HttpUrl = Field(default=None)
    ORCID: AnyUrl = Field(default=None)
    google_scholar_id: AnyUrl = Field(default=None)
    research_gate_id: AnyUrl = Field(default=None)

    _group_identifiers = root_validator(pre=True, allow_reuse=True)(split_user_identifiers)

    class Config:
        fields = {'name': {"rdf_predicate": HSTERMS.name},
                  'phone': {"rdf_predicate": HSTERMS.phone},
                  'address': {"rdf_predicate": HSTERMS.address},
                  'organization': {"rdf_predicate": HSTERMS.organization},
                  'email': {"rdf_predicate": HSTERMS.email},
                  'homepage': {"rdf_predicate": HSTERMS.homepage},
                  'ORCID': {"rdf_predicate": HSTERMS.ORCID},
                  'google_scholar_id': {"rdf_predicate": HSTERMS.GoogleScholarID},
                  'research_gate_id': {"rdf_predicate": HSTERMS.ResearchGateID}}


class AwardInfo(BaseModel):
    funding_agency_name: str = Field()
    title: str = Field(default=None)
    number: str = Field(default=None)
    funding_agency_url: AnyUrl = Field(default=None)


class AwardInfoInRDF(AwardInfo, RDFBaseModel):

    class Config:
        fields = {'funding_agency_name': {"rdf_predicate": HSTERMS.fundingAgencyName},
                  'title': {"rdf_predicate": HSTERMS.awardTitle},
                  'number': {"rdf_predicate": HSTERMS.awardNumber},
                  'funding_agency_url': {"rdf_predicate": HSTERMS.fundingAgencyURL}}


class BandInformation(BaseModel):
    name: str = Field(max_length=500)
    variable_name: str = Field(default=None, max_length=100)
    variable_unit: str = Field(default=None, max_length=50)

    no_data_value: str = Field(default=None)
    maximum_value: str = Field(default=None)
    comment: str = Field(default=None)
    method: str = Field(default=None)
    minimum_value: str = Field(default=None)


class BandInformationInRDF(BandInformation, RDFBaseModel):

    class Config:
        fields = {'name': {"rdf_predicate": HSTERMS.name},
                  'variable_name': {"rdf_predicate": HSTERMS.variableName},
                  'variable_unit': {"rdf_predicate": HSTERMS.variableUnit},
                  'no_data_value': {"rdf_predicate": HSTERMS.noDataValue},
                  'maximum_value': {"rdf_predicate": HSTERMS.maximumValue},
                  'comment': {"rdf_predicate": HSTERMS.comment},
                  'method': {"rdf_predicate": HSTERMS.method},
                  'minimum_value': {"rdf_predicate": HSTERMS.minimumValue}}


class CoverageInRDF(RDFBaseModel):
    type: CoverageType = Field(rdf_predicate=RDF.type)
    value: str = Field(rdf_predicate=RDF.value)


class SpatialReferenceInRDF(RDFBaseModel):
    type: SpatialReferenceType = Field(rdf_predicate=RDF.type)
    value: str = Field(rdf_predicate=RDF.value)


class MultidimensionalSpatialReferenceInRDF(RDFBaseModel):
    type: MultidimensionalSpatialReferenceType = Field(rdf_predicate=RDF.type)
    value: str = Field(rdf_predicate=RDF.value)


class FieldInformation(BaseModel):
    field_name: str = Field(max_length=128)
    field_type: str = Field(max_length=128)
    field_type_code: str = Field(default=None, max_length=50)
    field_width: int = Field(default=None)
    field_precision: int = Field(default=None)


class FieldInformationInRDF(FieldInformation, RDFBaseModel):

    class Config:
        fields = {'field_name': {"rdf_predicate": HSTERMS.fieldName},
                  'field_type': {"rdf_predicate": HSTERMS.fieldType},
                  'field_type_code': {"rdf_predicate": HSTERMS.fieldTypeCode},
                  'field_width': {"rdf_predicate": HSTERMS.fieldWidth},
                  'field_precision': {"rdf_predicate": HSTERMS.fieldPrecision}}


class GeometryInformation(BaseModel):
    feature_count: int = Field(default=0)
    geometry_type: str = Field(max_length=128)


class GeometryInformationInRDF(GeometryInformation, RDFBaseModel):

    class Config:
        fields = {'feature_count': {"rdf_predicate": HSTERMS.featureCount},
                  'geometry_type': {"rdf_predicate": HSTERMS.geometryType}}


class Variable(BaseModel):
    name: str = Field(max_length=1000)
    unit: str = Field(max_length=1000)
    type: VariableType = Field()
    shape: str = Field(max_length=1000)
    descriptive_name: str = Field(default=None, max_length=1000)
    method: str = Field(default=None)
    missing_value: str = Field(default=None, max_length=1000)


class VariableInRDF(Variable, RDFBaseModel):

    class Config:
        fields = {'name': {"rdf_predicate": HSTERMS.name},
                  'unit': {"rdf_predicate": HSTERMS.unit},
                  'type': {"rdf_predicate": HSTERMS.type},
                  'shape': {"rdf_predicate": HSTERMS.shape},
                  'descriptive_name': {"rdf_predicate": HSTERMS.descriptive_name},
                  'method': {"rdf_predicate": HSTERMS.method},
                  'missing_value': {"rdf_predicate": HSTERMS.missing_value}}


class Publisher(BaseModel):
    name: str = Field(max_length=200)
    url: AnyUrl = Field()


class PublisherInRDF(Publisher, RDFBaseModel):

    class Config:
        fields = {'name': {"rdf_predicate": HSTERMS.publisherName},
                  'url': {"rdf_predicate": HSTERMS.publisherURL}}


class TimeSeriesVariable(BaseModel):
    variable_code: str = Field(max_length=50)
    variable_name: str = Field(max_length=100)
    variable_type: str = Field(max_length=100)
    no_data_value: int = Field()
    variable_definition: str = Field(default=None, max_length=255)
    speciation: str = Field(default=None, max_length=255)


class TimeSeriesVariableInRDF(TimeSeriesVariable, RDFBaseModel):

    class Config:
        fields = {'variable_code': {"rdf_predicate": HSTERMS.VariableCode},
                  'variable_name': {"rdf_predicate": HSTERMS.VariableName},
                  'variable_type': {"rdf_predicate": HSTERMS.VariableType},
                  'no_data_value': {"rdf_predicate": HSTERMS.NoDataValue},
                  'variable_definition': {"rdf_predicate": HSTERMS.VariableDefinition},
                  'speciation': {"rdf_predicate": HSTERMS.Speciation}}


class TimeSeriesSite(BaseModel):
    site_code: str = Field(max_length=200)
    site_name: str = Field(default=None, max_length=255)
    elevation_m: float = Field(default=None)
    elevation_datum: str = Field(default=None, max_length=50)
    site_type: str = Field(default=None, max_length=100)
    latitude: float = Field(default=None)
    longitude: float = Field(default=None)


class TimeSeriesSiteInRDF(TimeSeriesSite, RDFBaseModel):

    class Config:
        fields = {'site_code': {"rdf_predicate": HSTERMS.SiteCode},
                  'site_name': {"rdf_predicate": HSTERMS.SiteName},
                  'elevation_m': {"rdf_predicate": HSTERMS.Elevation_m},
                  'elevation_datum': {"rdf_predicate": HSTERMS.ElevationDatum},
                  'site_type': {"rdf_predicate": HSTERMS.SiteType},
                  'latitude': {"rdf_predicate": HSTERMS.Latitude},
                  'longitude': {"rdf_predicate": HSTERMS.Longitude}}


class TimeSeriesMethod(BaseModel):
    method_code: str = Field(max_length=50)
    method_name: str = Field(max_length=200)
    method_type: str = Field(max_length=200)
    method_description: str = Field(default=None)
    method_link: AnyUrl = Field(default=None)


class TimeSeriesMethodInRDF(TimeSeriesMethod, RDFBaseModel):

    class Config:
        fields = {'method_code': {"rdf_predicate": HSTERMS.MethodCode},
                  'method_name': {"rdf_predicate": HSTERMS.MethodName},
                  'method_type': {"rdf_predicate": HSTERMS.MethodType},
                  'method_description': {"rdf_predicate": HSTERMS.MethodDescription},
                  'method_link': {"rdf_predicate": HSTERMS.MethodLink}}


class ProcessingLevel(BaseModel):
    processing_level_code: str = Field(max_length=50)
    definition: str = Field(default=None, max_length=200)
    explanation: str = Field(default=None)


class ProcessingLevelInRDF(ProcessingLevel, RDFBaseModel):

    class Config:
        fields = {'processing_level_code': {"rdf_predicate": HSTERMS.ProcessingLevelCode},
                  'definition': {"rdf_predicate": HSTERMS.Definition},
                  'explanation': {"rdf_predicate": HSTERMS.Explanation}}


class Unit(BaseModel):
    type: str = Field(max_length=255)
    name: str = Field(max_length=255)
    abbreviation: str = Field(max_length=20)


class UnitInRDF(Unit, RDFBaseModel):

    class Config:
        fields = {'type': {"rdf_predicate": HSTERMS.UnitsType},
                  'name': {"rdf_predicate": HSTERMS.UnitsName},
                  'abbreviation': {"rdf_predicate": HSTERMS.UnitsAbbreviation}}


class UTCOffSet(BaseModel):
    value: float = Field(default=0)


class UTCOffSetInRDF(UTCOffSet, RDFBaseModel):

    class Config:
        fields = {'value': {"rdf_predicate": HSTERMS.value}}


class TimeSeriesResult(BaseModel):
    series_id: str = Field(max_length=36)
    unit: Unit = Field(default=None)
    status: str = Field(default=None, max_length=255)
    sample_medium: str = Field(max_length=255)
    value_count: int = Field()
    aggregation_statistics: str = Field(max_length=255)
    series_label: str = Field(default=None, max_length=255)
    site: TimeSeriesSite = Field()
    variable: TimeSeriesVariable = Field()
    method: TimeSeriesMethod = Field()
    processing_level: ProcessingLevel = Field()
    utc_offset: UTCOffSet = Field(default=None)


class TimeSeriesResultInRDF(TimeSeriesResult, RDFBaseModel):

    unit: UnitInRDF = Field(rdf_predicate=HSTERMS.unit, default=None)
    site: TimeSeriesSiteInRDF = Field(rdf_predicate=HSTERMS.site)
    variable: TimeSeriesVariableInRDF = Field(rdf_predicate=HSTERMS.variable)
    method: TimeSeriesMethodInRDF = Field(rdf_predicate=HSTERMS.method)
    processing_level: ProcessingLevelInRDF = Field(rdf_predicate=HSTERMS.processingLevel)
    utc_offset: UTCOffSetInRDF = Field(rdf_predicate=HSTERMS.UTCOffSet, default=None)

    class Config:
        fields = {'series_id': {"rdf_predicate": HSTERMS.timeSeriesResultUUID},
                  'status': {"rdf_predicate": HSTERMS.Status},
                  'sample_medium': {"rdf_predicate": HSTERMS.SampleMedium},
                  'value_count': {"rdf_predicate": HSTERMS.ValueCount},
                  'aggregation_statistics': {"rdf_predicate": HSTERMS.AggregationStatistic},
                  'series_label': {"rdf_predicate": HSTERMS.SeriesLabel}}
