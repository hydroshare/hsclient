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


rdf_schemas = {ORE.ResourceMap: ResourceMap,
               HSTERMS.CompositeResource: ResourceMetadataInRDF,
               HSTERMS.GeographicRasterAggregation: GeographicRasterMetadataInRDF,
               HSTERMS.GeographicFeatureAggregation: GeographicFeatureMetadataInRDF,
               HSTERMS.MultidimensionalAggregation: MultidimensionalMetadataInRDF,
               HSTERMS.ReferencedTimeSeriesAggregation: ReferencedTimeSeriesMetadataInRDF,
               HSTERMS.FileSetAggregation: FileSetMetadataInRDF,
               HSTERMS.SingleFileAggregation: SingleFileMetadataInRDF}

user_schemas = {ResourceMetadataInRDF: ResourceMetadata,
                GeographicRasterMetadataInRDF: GeographicRasterMetadata,
                GeographicFeatureMetadataInRDF: GeographicFeatureMetadata,
                MultidimensionalMetadataInRDF: MultidimensionalMetadata,
                ReferencedTimeSeriesMetadataInRDF: ReferencedTimeSeriesMetadata,
                FileSetMetadataInRDF: FileSetMetadata,
                SingleFileMetadataInRDF: SingleFileMetadata}


def load_rdf(rdf_str, file_format='xml'):

    g = Graph().parse(data=rdf_str, format=file_format)
    for target_class, schema in rdf_schemas.items():
        subject = g.value(predicate=RDF.type, object=target_class)
        if subject:
            if target_class == ORE.ResourceMap:
                return _parse(schema, g)
            else:
                rdf_metadata = _parse(schema, g)
                if schema in user_schemas.keys():
                    return user_schemas[schema](**rdf_metadata.dict())
                return rdf_metadata
    raise Exception("Could not find schema for \n{}".format(rdf_str))


def parse_file(schema, file, file_format='xml', subject=None):
    metadata_graph = Graph().parse(file, format=file_format)
    return _parse(schema, metadata_graph, subject)


def rdf_graph(schema):
    for rdf_schema, user_schema in user_schemas.items():
        if isinstance(schema, user_schema):
            return _rdf_graph(rdf_schema(**schema.dict()), Graph())
    return _rdf_graph(schema, Graph())


def rdf_string(schema, rdf_format='pretty-xml'):
    return rdf_graph(schema).serialize(format=rdf_format).decode()


def _rdf_fields(schema):
    for f in schema.__fields__.values():
        if f.alias not in ['rdf_subject', 'rdf_type', 'label', 'dc_type']:
            yield f

def _rdf_graph(schema, graph=None):
    for f in _rdf_fields(schema):
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
                    graph = _rdf_graph(value, graph)
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


def _parse(schema, metadata_graph, subject=None):
    def nested_class(field):
        if field.sub_fields:
            clazz = get_args(field.outer_type_)[0]
        else:
            clazz = field.outer_type_
        if inspect.isclass(clazz):
            return issubclass(clazz, BaseModel)
        return False

    def class_rdf_type(schema):
        if schema.__fields__['rdf_type']:
            return schema.__fields__['rdf_type'].default
        return None

    if not subject:
        # lookup subject using RDF.type specified in the schema
        target_class = class_rdf_type(schema)
        if not target_class:
            raise Exception("Subject must be provided, no RDF.type specified on class {}".format(schema))
        subject = metadata_graph.value(predicate=RDF.type, object=target_class)
        if not subject:
            raise Exception("Could not find subject for predicate=RDF.type, object={}".format(target_class))
    kwargs = {}
    for f in _rdf_fields(schema):
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
                parsed_class = _parse(clazz, metadata_graph, value)
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
        instance = schema(**kwargs, rdf_subject=subject)
        return instance
    return None
