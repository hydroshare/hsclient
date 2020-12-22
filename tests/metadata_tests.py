import os
from datetime import datetime

import pytest
from rdflib import Graph

from hs_rdf.namespaces import RDF
from hs_rdf.schemas import load_rdf, rdf_graph
from rdflib.compare import _squashed_graphs_triples

from hs_rdf.schemas.enums import RelationType, UserIdentifierType
from hs_rdf.schemas.data_structures import PeriodCoverage, BoxCoverage, PointCoverage
from hs_rdf.utils import to_coverage_dict


@pytest.fixture()
def res_md():
    with open("data/metadata/resourcemetadata.xml", 'r') as f:
        return load_rdf(f.read())


@pytest.fixture()
def res_md_point():
    with open("data/metadata/resourcemetadata_with_point_coverage.xml", 'r') as f:
        return load_rdf(f.read())


def compare_graphs(new_graph, original_graph):
        for (new_triple, original_triple) in _squashed_graphs_triples(new_graph, original_graph):
            if new_triple[1] == RDF.value:
                # for coverage and spatial reference, the value string needs to be parsed into a dictionary for comparison
                if ';' in new_triple[2]:
                    assert new_triple[0] == original_triple[0]
                    assert new_triple[1] == original_triple[1]
                    assert to_coverage_dict(new_triple[2]) == to_coverage_dict(original_triple[2])
            else:
                assert new_triple == original_triple


def compare_metadatas(new_graph, original_metadata_file):
        original_graph = Graph()
        with open(original_metadata_file, "r") as f:
            original_graph = original_graph.parse(data=f.read())
        compare_graphs(new_graph, original_graph)

metadata_files = ['resourcemetadata.xml', 'logan_meta.xml', 'asdf_meta.xml', 'msf_version.refts_meta.xml',
                  'SWE_time_meta.xml', 'test_meta.xml', 'watersheds_meta.xml', 'ODM2_Multi_Site_One_Variable_meta.xml']
#metadata_files = ['resourcemetadata.xml']
@pytest.mark.parametrize("metadata_file", metadata_files)
def test_resource_serialization(metadata_file):
    metadata_file = os.path.join('data', 'metadata', metadata_file)
    with open(metadata_file, 'r') as f:
        md = load_rdf(f.read())
    g = rdf_graph(md)
    rdf_string = g.serialize(format="pretty-xml").decode()
    compare_metadatas(g, metadata_file)

def test_resource_metadata(res_md):

    assert res_md.title == "sadfadsgasdf"

    assert len(res_md.subjects) == 14
    assert "key1" in res_md.subjects
    assert "key2" in res_md.subjects
    assert "asdf" in res_md.subjects
    assert "Snow water equivalent" in res_md.subjects

    assert res_md.abstract == "sadfasdfsadfa"

    assert res_md.language == "eng"

    assert res_md.identifier == "http://www.hydroshare.org/resource/84805fd615a04d63b4eada65644a1e20"

    assert len(res_md.additional_metadata) == 2
    assert "key2" in res_md.additional_metadata
    assert res_md.additional_metadata["key2"] == "value2"

    assert len(res_md.sources) == 2
    assert "another" in res_md.sources
    assert "the source" in res_md.sources

    assert len(res_md.creators) == 3
    creator = res_md.creators[0]
    assert creator.organization == 'Utah State University'
    assert creator.email == 'jeff.horsburgh@usu.edu'
    creator = res_md.creators[1]
    assert not creator.organization
    assert not creator.email
    assert creator.name == 'Tseganeh Z. Gichamo'
    creator = res_md.creators[2]
    assert creator.organization == 'USU'
    assert creator.email == 'scott.black@usu.edu'

    try:
        res_md.creators = []
        assert False, "should have thrown exception"
    except ValueError as e:
        assert "list must contain at least one entry" in str(e)

    assert len(res_md.contributors) == 2
    contributor = next(x for x in res_md.contributors if x.email == "dtarb@usu.edu")
    assert contributor
    assert contributor.phone == "tel:4357973172"
    assert contributor.address == "Utah, US"
    assert contributor.homepage == "http://hydrology.usu.edu/dtarb"
    assert contributor.organization == "Utah State University"
    assert contributor.identifiers[UserIdentifierType.ORCID] == "https://orcid.org/0000-0002-1998-3479"
    assert contributor.name == "David Tarboton"

    assert len(res_md.relations) == 3
    assert any(x for x in res_md.relations if x.value == "https://sadf.com" and x.type == RelationType.isPartOf)
    assert any(x for x in res_md.relations if x.value == "https://www.google.com" and x.type== RelationType.isCopiedFrom)

    assert res_md.rights.statement == "my statement"
    assert res_md.rights.url == "http://studio.bakajo.com"

    assert res_md.modified == datetime.fromisoformat("2020-11-13T19:40:57.276064+00:00")
    assert res_md.created == datetime.fromisoformat("2020-07-09T19:12:21.354703+00:00")
    assert res_md.published == datetime.fromisoformat("2020-11-13T18:53:19.778819+00:00")

    assert len(res_md.awards) == 2
    award = next(x for x in res_md.awards if x.award_title == "t")
    assert award
    assert award.award_number == "n"
    assert award.funding_agency_name == "agency1"
    assert award.funding_agency_url == "https://google.com"

    res_md.period_coverage == PeriodCoverage(start=datetime.fromisoformat("2020-07-10T00:00:00"),
                                             end=datetime.fromisoformat("2020-07-29T00:00:00"))

    res_md.spatial_coverage == BoxCoverage(name="asdfsadf", northlimit=42.1505, eastlimit=-84.5739,
                                           projection='WGS 84 EPSG:4326', southlimit=30.282,
                                           type='box', units='Decimal Degrees', westlimit=-104.7887)

    pc = PointCoverage(name='Logan, Utah', north=41.7371, east=-111.8351,
                                            projection='WGS 84 EPSG:4326', type='point',
                                            units='Decimal degrees')

    res_md.spatial_coverage = pc

    assert res_md.publisher
    assert res_md.publisher.name == "Consortium of Universities for the Advancement of Hydrologic Science, Inc. (CUAHSI)"
    assert res_md.publisher.url == "https://www.cuahsi.org"





