from rdflib import Graph

from hs_rdf.namespaces import ORE, HSTERMS, RDF
from hs_rdf.schemas.aggregations import GeographicRasterMetadataInRDF, GeographicFeatureMetadataInRDF, \
    MultidimensionalMetadataInRDF, \
    ReferencedTimeSeriesMetadataInRDF, FileSetMetadataInRDF, SingleFileMetadataInRDF, GeographicRasterMetadata
from hs_rdf.schemas.resource import ResourceMap, ResourceMetadataInRDF, ResourceMetadata


def load_rdf(rdf_str, file_format='xml'):
    schemas = {ORE.ResourceMap: ResourceMap,
               #HSTERMS.CompositeResource: ResourceMetadataInRDF,
               HSTERMS.CompositeResource: ResourceMetadata,
               #HSTERMS.GeographicRasterAggregation: GeographicRasterMetadataInRDF,
               HSTERMS.GeographicRasterAggregation: GeographicRasterMetadata,
               HSTERMS.GeographicFeatureAggregation : GeographicFeatureMetadataInRDF,
               HSTERMS.MultidimensionalAggregation : MultidimensionalMetadataInRDF,
               HSTERMS.ReferencedTimeSeriesAggregation : ReferencedTimeSeriesMetadataInRDF,
               HSTERMS.FileSetAggregation : FileSetMetadataInRDF,
               HSTERMS.SingleFileAggregation : SingleFileMetadataInRDF}
    g = Graph().parse(data=rdf_str, format=file_format)
    for target_class, schema in schemas.items():
        subject = g.value(predicate=RDF.type, object=target_class)
        if subject:
            return schema.parse(g)
    raise Exception("Could not find schema for \n{}".format(rdf_str))