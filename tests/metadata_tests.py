import os

import pytest
from rdflib import Graph, URIRef, Literal

from hs_rdf.implementations.hydroshare import Resource, AggregationType
from hs_rdf.namespaces import HSTERMS, HSRESOURCE, DCTERMS, RDFS1, RDF
from hs_rdf.schemas import load_rdf
from rdflib.compare import _squashed_graphs_triples

from hs_rdf.schemas.fields import DateType, CoverageType


@pytest.fixture()
def res_md():
    with open("data/metadata/resourcemetadata.xml", 'r') as f:
        return load_rdf(f.read())


def to_coverage_dict(value):
    value_dict = {}
    for key_value in value.split("; "):
        k, v = key_value.split("=")
        if k == 'units':
            value_dict['unit'] = v
        else:
            value_dict[k] = v
    return value_dict


def compare_metadatas(new_graph, original_metadata_file):
        original_graph = Graph()
        with open(original_metadata_file, "r") as f:
            original_graph = original_graph.parse(data=f.read())

        for (new_triple, original_triple) in _squashed_graphs_triples(new_graph, original_graph):
            if new_triple[1] == RDF.value:
                # for coverage and spatial reference, the value string needs to be parsed into a dictionary for comparison
                if ';' in new_triple[2]:
                    assert new_triple[0] == original_triple[0]
                    assert new_triple[1] == original_triple[1]
                    assert to_coverage_dict(new_triple[2]) == to_coverage_dict(original_triple[2])
            else:
                assert new_triple == original_triple

metadata_files = ['resourcemetadata.xml', 'asdf_meta.xml', 'logan_meta.xml', 'msf_version.refts_meta.xml',
                  'SWE_time_meta.xml', 'test_meta.xml', 'watersheds_meta.xml']

@pytest.mark.parametrize("metadata_file", metadata_files)
def test_resource_serialization(metadata_file):
    metadata_file = os.path.join('data', 'metadata', metadata_file)
    with open(metadata_file, 'r') as f:
        md = load_rdf(f.read())
    g = Graph()
    md.rdf(g)
    compare_metadatas(g, metadata_file)

def test_resource_metadata(res_md):
    assert res_md.rdf_subject == getattr(HSRESOURCE, "84805fd615a04d63b4eada65644a1e20")

    assert res_md.title == "sadfadsgasdf"

    assert len(res_md.subjects) == 14
    assert "key1" in res_md.subjects
    assert "key2" in res_md.subjects
    assert "asdf" in res_md.subjects
    assert "Snow water equivalent" in res_md.subjects

    assert res_md.description.abstract == "sadfasdfsadfa"

    assert res_md.language == "eng"

    assert str(res_md.dc_type) == "https://www.hydroshare.org/terms/CompositeResource"

    assert res_md.identifier.hydroshare_identifier == "http://www.hydroshare.org/resource/84805fd615a04d63b4eada65644a1e20"

    assert len(res_md.extended_metadatas) == 2
    assert next(filter(lambda x: x.key == "key2", res_md.extended_metadatas)).value == "value2"

    assert len(res_md.sources) == 2
    assert any(x for x in res_md.sources if x.is_derived_from == 'another')

    assert len(res_md.formats) == 11
    assert any(x for x in res_md.formats if x.value == 'application/dbf')

    assert len(res_md.creators) == 2
    creator = next(x for x in res_md.creators if x.name == "Scott s Black")
    assert creator
    assert creator.organization == 'USU'
    assert creator.email == 'scott.black@usu.edu'
    assert creator.creator_order == 1

    assert len(res_md.contributors) == 2
    contributor = next(x for x in res_md.contributors if x.email == "dtarb@usu.edu")
    assert contributor
    assert contributor.phone == "tel:4357973172"
    assert contributor.address == "Utah, US"
    assert contributor.homepage == "http://hydrology.usu.edu/dtarb"
    assert contributor.organization == "Utah State University"
    assert contributor.ORCID == "https://orcid.org/0000-0002-1998-3479"
    assert contributor.name == "David Tarboton"

    assert len(res_md.sources) == 2
    assert any(x for x in res_md.sources if x.is_derived_from == "the source")

    assert len(res_md.relations) == 2
    assert any(x for x in res_md.relations if x.is_part_of == "https://sadf.com")
    assert any(x for x in res_md.relations if x.is_copied_from == "https://www.google.com")

    assert res_md.rights.rights_statement == "my statement"
    assert res_md.rights.url == "http://studio.bakajo.com"

    assert len(res_md.dates) == 2
    modified = next(x for x in res_md.dates if x.type == DateType.modified)
    assert modified
    # TODO need to handle timezones in dates
    assert str(modified.value) == "2020-11-13 19:40:57.276064+00:00"
    created = next(x for x in res_md.dates if x.type == DateType.created)
    assert created
    assert str(created.value) == "2020-07-09 19:12:21.354703+00:00"

    assert len(res_md.award_infos) == 2
    award = next(x for x in res_md.award_infos if x.award_title == "t")
    assert award
    assert award.award_number == "n"
    assert award.funding_agency_name == "agency1"
    assert award.funding_agency_url == "https://google.com"

    assert len(res_md.coverages) == 2
    box = next(x for x in res_md.coverages if x.type == CoverageType.box)
    # TODO update coverage to parse values
    assert box.value == "name=asdfsadf; northlimit=42.1505; eastlimit=-84.5739; southlimit=30.282; westlimit=-104.7887; units=Decimal degrees; projection=WGS 84 EPSG:4326"
    period = next(x for x in res_md.coverages if x.type == CoverageType.period)
    assert period.value == "start=2020-07-10T00:00:00; end=2020-07-29T00:00:00"

