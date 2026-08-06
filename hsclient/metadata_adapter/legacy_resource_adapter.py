from hsclient.metadata_adapter.resource_models import SchemaOrgResourceMetadata
from hsclient.metadata_adapter.legacy_resource_models import LegacyResourceMetadata
from hsclient.schema import base as schema


class LegacyResourceMetadataAdapter(LegacyResourceMetadata):
    """This adapter takes legacy resource metadata and converts it to schema.org format.
       This adapter is used for saving user edited legacy resource metadata in schema.org format,
       (as user resource metadata) to write to s3.
    """
    def to_dataset_creators(self):
        creators = []
        if not self.creators:
            raise ValueError("creators list must have at least one creator")
        for creator in self.creators:
            creators.append(creator.to_dataset_creator())
        return creators

    def to_dataset_contributors(self):
        contributors = []
        for contributor in self.contributors:
            contributors.append(contributor.to_dataset_contributor())
        return contributors

    def to_dataset_funding(self):
        grants = []
        for award in self.awards:
            grants.append(award.to_dataset_grant())
        return grants

    def to_dataset_associated_media(self):
        return self.associatedMedia

    def to_dataset_is_part_of(self):
        return self._to_dataset_part_relations("IsPartOf")

    def to_dataset_has_part(self):
        return self._to_dataset_part_relations("HasPart")

    def to_dataset_relation(self):
        relations = []
        for relation in self.relations:
            relations.append(relation.to_dataset_relation())
        return relations

    def _to_dataset_part_relations(self, relation_type: str):
        part_relations = []
        for relation in self.relations:
            part_relation = relation.to_dataset_part_relation(relation_type)
            if part_relation:
                part_relations.append(part_relation)
        return part_relations

    def to_dataset_spatial_coverage(self):
        if self.spatial_coverage:
            return self.spatial_coverage.to_dataset_spatial_coverage()
        return None

    def to_dataset_period_coverage(self):
        if self.period_coverage:
            return self.period_coverage.to_dataset_temporal_coverage()
        return None

    def to_dataset_keywords(self):
        if self.subjects:
            return self.subjects
        return ["HydroShare"]

    def to_dataset_license(self):
        if self.rights:
            return self.rights.to_dataset_license()

    def to_dataset_creative_work_status(self):
        status_defined_terms = {
            "public": schema.Public,
            "published": schema.Published,
            "discoverable": schema.Discoverable,
            "private": schema.Private,
        }
        if self.sharing_status:
            return status_defined_terms[self.sharing_status].model_construct()

    def to_dataset_additional_properties(self):
        additional_properties = []
        if self.additional_metadata:
            for key, value in self.additional_metadata.items():
                property_value = schema.PropertyValue.model_construct()
                property_value.name = key
                property_value.value = value
                additional_properties.append(property_value)
        return additional_properties

    @staticmethod
    def to_dataset_provider():
        provider = schema.Organization.model_construct()
        provider.name = "HydroShare"
        provider.url = "https://www.hydroshare.org/"
        return provider

    def to_resource_metadata(self):
        # Generate resource metadata in schema.org format from the legacy resource metadata
        dataset = SchemaOrgResourceMetadata.model_construct(**self.extra_columns)
        dataset.additionalType = self.type
        dataset.provider = self.to_dataset_provider()
        dataset.name = self.title
        dataset.description = self.abstract
        dataset.url = self.url
        dataset.identifier = [str(self.identifier)] if self.identifier else []
        dataset.creator = self.to_dataset_creators()
        dataset.contributor = self.to_dataset_contributors()
        dataset.dateCreated = self.created
        dataset.dateModified = self.modified
        dataset.datePublished = self.published
        dataset.keywords = self.to_dataset_keywords()
        dataset.inLanguage = self.language
        dataset.funding = self.to_dataset_funding()
        dataset.spatialCoverage = self.to_dataset_spatial_coverage()
        dataset.temporalCoverage = self.to_dataset_period_coverage()
        dataset.associatedMedia = self.to_dataset_associated_media()
        dataset.isPartOf = self.isPartOf
        dataset.hasPart = self.hasPart
        if self.publisher:
            dataset.publisher = self.publisher.to_dataset_publisher()
        dataset.license = self.to_dataset_license()
        dataset.citation = [self.citation]
        dataset.creativeWorkStatus = self.to_dataset_creative_work_status()
        dataset.relation = self.to_dataset_relation()
        dataset.additionalProperty = self.to_dataset_additional_properties()
        return dataset
