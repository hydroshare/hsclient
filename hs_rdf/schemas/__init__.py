import inspect
from datetime import datetime
from enum import Enum

from pydantic import AnyUrl, BaseModel
from rdflib import Graph, URIRef, Literal
from typing import get_args

from hs_rdf.namespaces import ORE, HSTERMS, RDF, XSD, DC, RDFS1
from hs_rdf.schemas.aggregations import GeographicRasterMetadataInRDF, GeographicFeatureMetadataInRDF, \
    MultidimensionalMetadataInRDF, \
    ReferencedTimeSeriesMetadataInRDF, FileSetMetadataInRDF, SingleFileMetadataInRDF, GeographicRasterMetadata, \
    GeographicFeatureMetadata, MultidimensionalMetadata, ReferencedTimeSeriesMetadata, FileSetMetadata, \
    SingleFileMetadata
from hs_rdf.schemas.enums import AnyUrlEnum
from hs_rdf.schemas.resource import ResourceMap, ResourceMetadataInRDF, ResourceMetadata


def nested_class(field):
    if field.sub_fields:
        clazz = get_args(field.outer_type_)[0]
    else:
        clazz = field.outer_type_
    if inspect.isclass(clazz):
        return issubclass(clazz, BaseModel)
    return False


def rdf_fields(schema):
    for f in schema.__fields__.values():
        if f.alias not in ['rdf_subject', 'rdf_type', 'label', 'dc_type']:
            yield f


def rdf_type(schema):
    for f in schema.__fields__.values():
        if f.alias == 'rdf_type':
            return f
    return None


def class_rdf_type(schema):
    if schema.__fields__['rdf_type']:
        return schema.__fields__['rdf_type'].default
    return None

def rdf(schema, graph=None):
    if not graph:
        graph = Graph()
    for f in rdf_fields(schema):
        predicate = f.field_info.extra['rdf_predicate']
        values = getattr(schema, f.name, None)
        if values:
            if not isinstance(values, list):
                # handle single values as a list to simplify
                values = [values]
            for value in values:
                if isinstance(value, BaseModel):
                    assert hasattr(value, "rdf_subject")
                    # nested class
                    graph.add((schema.rdf_subject, predicate, value.rdf_subject))
                    graph = rdf(value, graph)
                else:
                    # primitive value
                    if isinstance(value, AnyUrl):
                        value = URIRef(value)
                    elif isinstance(value, datetime):
                        value = Literal(value.isoformat())
                    elif isinstance(value, int):
                        value = Literal(value, datatype=XSD.integer)
                    elif isinstance(value, float):
                        value = Literal(value, datatype=XSD.double)
                    elif isinstance(value, AnyUrlEnum):
                        value = URIRef(value.value)
                    elif isinstance(value, Enum):
                        value = Literal(value.value)
                    else:
                        value = Literal(value)
                    graph.add((schema.rdf_subject, predicate, value))
    if hasattr(schema, 'rdf_type'):
        graph.add((schema.rdf_subject, RDF.type, schema.rdf_type))
    if hasattr(schema, 'dc_type'):
        graph.add((schema.rdf_subject, DC.type, schema.dc_type))
    if hasattr(schema, 'label'):
        graph.add((URIRef(str(schema.rdf_type)), RDFS1.label, Literal(schema.label)))
        graph.add((URIRef(str(schema.rdf_type)), RDFS1.isDefinedBy, URIRef("https://www.hydroshare.org/terms/")))
    return graph


def rdf_string(schema, rdf_format='pretty-xml'):
    g = Graph()
    return rdf(schema, g).serialize(format=rdf_format).decode()


def parse_file(schema, file, file_format='xml', subject=None):
    metadata_graph = Graph().parse(file, format=file_format)
    return parse(schema, metadata_graph, subject)


def parse(schema, metadata_graph, subject=None):
    if not subject:
        # lookup subject using RDF.type specified in the schema
        target_class = class_rdf_type(schema)
        if not target_class:
            raise Exception("Subject must be provided, no RDF.type specified on class {}".format(schema))
        subject = metadata_graph.value(predicate=RDF.type, object=target_class)
        if not subject:
            raise Exception("Could not find subject for predicate=RDF.type, object={}".format(target_class))
    kwargs = {}
    for f in rdf_fields(schema):
        predicate = f.field_info.extra['rdf_predicate']
        if not predicate:
            raise Exception("Schema configuration error for {}, all fields must specify a rdf_predicate".format(schema))
        parsed = []
        for value in metadata_graph.objects(subject=subject, predicate=predicate):
            if nested_class(f):
                if f.sub_fields:
                    # list
                    clazz = f.sub_fields[0].outer_type_
                else:
                    # single
                    clazz = f.outer_type_
                parsed_class = parse(clazz, metadata_graph, value)
                if parsed_class:
                    parsed.append(parsed_class)
                elif f.sub_fields:
                    parsed.append([])
            else:
                # primitive value
                parsed.append(str(value))
        if len(parsed) > 0:
            if f.sub_fields:
                # list
                kwargs[f.name] = parsed
            else:
                # single
                kwargs[f.name] = parsed[0]
    if kwargs:
        instance = schema(**kwargs)
        instance.rdf_subject = subject
        return instance
    return None


def load_rdf(rdf_str, file_format='xml'):
    schemas = {ORE.ResourceMap: ResourceMap,
               HSTERMS.CompositeResource: ResourceMetadata,
               HSTERMS.GeographicRasterAggregation: GeographicRasterMetadata,
               HSTERMS.GeographicFeatureAggregation : GeographicFeatureMetadata,
               HSTERMS.MultidimensionalAggregation : MultidimensionalMetadata,
               HSTERMS.ReferencedTimeSeriesAggregation : ReferencedTimeSeriesMetadata,
               HSTERMS.FileSetAggregation : FileSetMetadata,
               HSTERMS.SingleFileAggregation : SingleFileMetadata}

    g = Graph().parse(data=rdf_str, format=file_format)
    for target_class, schema in schemas.items():
        subject = g.value(predicate=RDF.type, object=target_class)
        if subject:
            rdf_metadata = parse(schema._rdf_model_class, g)
            instance = schema(**rdf_metadata.dict())
            return instance
    raise Exception("Could not find schema for \n{}".format(rdf_str))
