import inspect

from typing import get_args
from datetime import datetime

from rdflib import Graph, BNode, URIRef, Literal
from rdflib.term import Identifier as RDFIdentifier
from pydantic import BaseModel, Field, AnyUrl

from hs_rdf.namespaces import RDF, RDFS1, XSD, DC


class RDFBaseModel(BaseModel):

    rdf_subject: RDFIdentifier = Field(default_factory=BNode)

    @classmethod
    def _rdf_fields(cls):
        for f in cls.__fields__.values():
            if f.alias not in ['rdf_subject', 'rdf_type', 'label', 'dc_type']:
                yield f

    @classmethod
    def _rdf_type(cls):
        for f in cls.__fields__.values():
            if f.alias == 'rdf_type':
                return f
        return None

    @classmethod
    def class_rdf_type(cls):
        if cls.__fields__['rdf_type']:
            return cls.__fields__['rdf_type'].default
        return None

    def rdf(self, graph):
        for f in self._rdf_fields():
            predicate = f.field_info.extra['rdf_predicate']
            values = getattr(self, f.name, None)
            if values:
                if not isinstance(values, list):
                    # handle single values as a list to simplify
                    values = [values]
                for value in values:
                    if isinstance(value, RDFBaseModel):
                        # nested class
                        graph.add((self.rdf_subject, predicate, value.rdf_subject))
                        graph = value.rdf(graph)
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
                        else:
                            value = Literal(value)
                        graph.add((self.rdf_subject, predicate, value))
        if hasattr(self, 'rdf_type'):
            graph.add((self.rdf_subject, RDF.type, self.rdf_type))
        if hasattr(self, 'dc_type'):
            graph.add((self.rdf_subject, DC.type, self.dc_type))
        if hasattr(self, 'label'):
            graph.add((URIRef(str(self.rdf_type)), RDFS1.label, Literal(self.label)))
            graph.add((URIRef(str(self.rdf_type)), RDFS1.isDefinedBy, URIRef("https://www.hydroshare.org/terms/")))
        return graph

    def rdf_string(self, rdf_format='ttl'):
        g = Graph()
        return self.rdf(g).serialize(format=rdf_format).decode()

    @classmethod
    def parse_file(cls, file, file_format='ttl', subject=None):
        metadata_graph = Graph().parse(file, format=file_format)
        return cls.parse(metadata_graph, subject)

    @classmethod
    def parse(cls, metadata_graph, subject=None):
        schema = cls
        if not subject:
            # lookup subject using RDF.type specified in the schema
            target_class = schema.class_rdf_type()
            if not target_class:
                raise Exception("Subject must be provided, no RDF.type specified on class {}".format(cls))
            subject = metadata_graph.value(predicate=RDF.type, object=target_class)
            if not subject:
                raise Exception("Could not find subject for predicate=RDF.type, object={}".format(target_class))
        kwargs = {'rdf_subject': subject}
        for f in schema._rdf_fields():
            predicate = f.field_info.extra['rdf_predicate']
            if not predicate:
                raise Exception("Schema configuration error for {}, all fields must specify a rdf_predicate".format(cls))
            parsed = []
            for value in metadata_graph.objects(subject=subject, predicate=predicate):
                if nested_class(f):
                    if f.sub_fields:
                        # list
                        clazz = f.sub_fields[0].outer_type_
                    else:
                        # single
                        clazz = f.outer_type_
                    parsed.append(clazz.parse(metadata_graph, value))
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
        return schema(**kwargs)

def nested_class(field):
    if field.sub_fields:
        clazz = get_args(field.outer_type_)[0]
    else:
        clazz = field.outer_type_
    if inspect.isclass(clazz):
        return issubclass(clazz, RDFBaseModel)
    return False




