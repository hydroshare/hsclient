from rdflib import Graph

from hs_rdf.namespaces import ORE, HSTERMS, RDF
from hs_rdf.schemas.aggregations import GeographicRasterMetadata, GeographicFeatureMetadata, MultidimensionalMetadata, \
    ReferencedTimeSeriesMetadata, FileSetMetadata, SingleFileMetadata
from hs_rdf.schemas.resource import ResourceMap, ResourceMetadata


def load_rdf(file, file_format):
    schemas = {ORE.ResourceMap: ResourceMap,
               HSTERMS.resource: ResourceMetadata,
               HSTERMS.GeographicRasterAggregation: GeographicRasterMetadata,
               HSTERMS.GeographicFeatureAggregation : GeographicFeatureMetadata,
               HSTERMS.MultidimensionalAggregation : MultidimensionalMetadata,
               HSTERMS.ReferencedTimeSeriesAggregation : ReferencedTimeSeriesMetadata,
               HSTERMS.FileSetAggregation : FileSetMetadata,
               HSTERMS.SingleFileAggregation : SingleFileMetadata}
    g = Graph().parse(file, format=file_format)
    for target_class, schema in schemas.items():
        subject = g.value(predicate=RDF.type, object=target_class)
        if subject:
            return schema.parse(g)