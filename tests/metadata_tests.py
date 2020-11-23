import os
from datetime import datetime

import pytest
from rdflib import Graph, URIRef, Literal

from hs_rdf.implementations.hydroshare import Resource, AggregationType
from hs_rdf.namespaces import HSTERMS, HSRESOURCE, DCTERMS, RDFS1, RDF
from hs_rdf.schemas import load_rdf, GeographicRasterMetadata
from rdflib.compare import _squashed_graphs_triples

from hs_rdf.schemas.fields import DateType, CoverageType
from hs_rdf.schemas.resource import PeriodCoverage, BoxCoverage, ResourceMetadata
from hs_rdf.utils import to_coverage_dict


@pytest.fixture()
def res_md():
    with open("data/metadata/resourcemetadata.xml", 'r') as f:
        return load_rdf(f.read())


@pytest.fixture()
def res_md_point():
    with open("data/metadata/resourcemetadata_with_point_coverage.xml", 'r') as f:
        return load_rdf(f.read())


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
    if isinstance(md, ResourceMetadata) or isinstance(md, GeographicRasterMetadata):
        md._sync()
        md._rdf_model.rdf(g)
    else:
        md.rdf(g)
    compare_metadatas(g, metadata_file)

def test_resource_metadata(res_md):
    #assert res_md._rdf_subject == getattr(HSRESOURCE, "84805fd615a04d63b4eada65644a1e20")

    assert res_md.title == "sadfadsgasdf"

    assert len(res_md.subjects) == 14
    assert "key1" in res_md.subjects
    assert "key2" in res_md.subjects
    assert "asdf" in res_md.subjects
    assert "Snow water equivalent" in res_md.subjects

    assert res_md.abstract == "sadfasdfsadfa"

    assert res_md.language == "eng"

    #assert str(res_md.dc_type) == "https://www.hydroshare.org/terms/CompositeResource"

    assert res_md.identifier == "http://www.hydroshare.org/resource/84805fd615a04d63b4eada65644a1e20"

    assert len(res_md.additional_metadata) == 2
    assert "key2" in res_md.additional_metadata
    assert res_md.additional_metadata["key2"] == "value2"

    assert len(res_md.derived_from) == 2
    assert "another" in res_md.derived_from
    assert "the source" in res_md.derived_from

    assert len(res_md.file_formats) == 11
    assert 'application/dbf' in res_md.file_formats

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

    assert len(res_md.relations) == 2
    assert any(x for x in res_md.relations if x.is_part_of == "https://sadf.com")
    assert any(x for x in res_md.relations if x.is_copied_from == "https://www.google.com")

    assert res_md.rights.rights_statement == "my statement"
    assert res_md.rights.url == "http://studio.bakajo.com"

    assert res_md.modified == datetime.fromisoformat("2020-11-13T19:40:57.276064+00:00")
    assert res_md.created == datetime.fromisoformat("2020-07-09T19:12:21.354703+00:00")
    assert res_md.published == datetime.fromisoformat("2020-11-13T18:53:19.778819+00:00")

    assert len(res_md.award_infos) == 2
    award = next(x for x in res_md.award_infos if x.award_title == "t")
    assert award
    assert award.award_number == "n"
    assert award.funding_agency_name == "agency1"
    assert award.funding_agency_url == "https://google.com"

    res_md.period_coverage == PeriodCoverage(start=datetime.fromisoformat("2020-07-10T00:00:00"),
                                             end=datetime.fromisoformat("2020-07-29T00:00:00"))

    res_md.spatial_coverage == BoxCoverage(name="asdfsadf", northlimit=42.1505, eastlimit=-84.5739,
                                           projection='WGS 84 EPSG:4326', southlimit=30.282,
                                           type='box', units='Decimal Degrees', westlimit=-104.7887)

    assert res_md.publisher
    assert res_md.publisher.name == "Consortium of Universities for the Advancement of Hydrologic Science, Inc. (CUAHSI)"
    assert res_md.publisher.url == "https://www.cuahsi.org"




