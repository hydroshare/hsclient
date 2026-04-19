from datetime import datetime

from hsmodels.schemas.fields import (
    AwardInfo,
	BoxCoverage,
	PointCoverage,
	Contributor,
	Creator,
	PeriodCoverage,
	Relation,
	Rights,
)
from hsmodels.schemas.enums import RelationType

def test_update_resource_metadata(hydroshare) -> None:
	"""
	Test updating resource metadata for a HydroShare resource using hsclient.
	This is to ensure that the resource metadata editing API has not changed in hsclient due to source metadata
	being in schema.org format.
	"""
	hs = hydroshare
	new_res = None
	try:
		new_res = hs.create()
		assert new_res.metadata.title == "Untitled resource"
		assert len(new_res.resource_id) == 32
		assert len(new_res.metadata.creators) == 1
		assert len(new_res.metadata.contributors) == 0
		assert len(new_res.metadata.awards) == 0
		assert len(new_res.metadata.relations) == 0
		assert new_res.metadata.spatial_coverage is None
		assert new_res.metadata.period_coverage is None
		assert new_res.metadata.rights is not None
		assert new_res.metadata.relations == []
		assert new_res.metadata.citation is not None
		assert new_res.metadata.additional_metadata == {}
		assert len(new_res.metadata.associatedMedia) == 1
		assert new_res.metadata.associatedMedia[0].contentUrl.endswith(
			f"/{new_res.resource_id}/.hsjsonld/file_manifest.json"
		)
		assert new_res.metadata.publisher is None
		assert new_res.metadata.sharing_status == "private"
		assert new_res.metadata.created is not None
		assert new_res.metadata.modified is not None
		assert new_res.metadata.published is None
		# update the resource metadata
		new_res.metadata.title = "Resource Metadata Editing Example"
		new_res.metadata.abstract = (
			"This resource demonstrates how to update metadata for a HydroShare resource using hsclient."
		)
		new_res.metadata.subjects = ["hsclient", "HydroShare", "metadata"]

		new_res.metadata.spatial_coverage = BoxCoverage(
			name="Logan, Utah",
			northlimit=41.7910,
			eastlimit=-111.7664,
			southlimit=41.6732,
			westlimit=-111.9079,
			projection="WGS 84 EPSG:4326",
			type="box",
			units="Decimal degrees",
		)
		new_res.metadata.period_coverage = PeriodCoverage(
			start=datetime.strptime("2024-01-01T00:00:00", "%Y-%m-%dT%H:%M:%S"),
			end=datetime.strptime("2024-01-31T00:00:00", "%Y-%m-%dT%H:%M:%S"),
		)

		new_res.metadata.additional_metadata = {
			"Observed Variable": "Temperature",
			"Site Location": "Logan, Utah",
		}

		new_res.metadata.relations.append(
			Relation(
				type=RelationType.isReferencedBy,
				value="Example article, https://example.com/article",
			)
		)

		new_res.metadata.awards.append(
			AwardInfo(
				funding_agency_name="National Science Foundation",
				title="Example Funding Award",
				number="NSF-123456",
				funding_agency_url="https://www.nsf.gov",
			)
		)

		new_res.metadata.creators.append(
			Creator(
				name="Doe, Jane",
				organization="Example University",
				email="jane.doe@example.com",
			)
		)

		new_res.metadata.contributors.append(
			Contributor(
				name="Smith, Alex",
				organization="Example Lab",
				email="alex.smith@example.com",
			)
		)

		new_res.metadata.rights = Rights(
			statement="Creative Commons Attribution 4.0 International",
			url="https://creativecommons.org/licenses/by/4.0/",
		)

		new_res.save()
		# sleep(1)  # wait for the resource to be saved and the metadata to be updated in HydroShare

		assert new_res.metadata.title == "Resource Metadata Editing Example"
		assert (
			new_res.metadata.abstract
			== "This resource demonstrates how to update metadata for a HydroShare resource using hsclient."
		)
		assert new_res.metadata.subjects == ["hsclient", "HydroShare", "metadata"]
		assert new_res.metadata.additional_metadata == {
			"Observed Variable": "Temperature",
			"Site Location": "Logan, Utah",
		}
		assert len(new_res.metadata.relations) == 1
		assert new_res.metadata.relations[0].type == RelationType.isReferencedBy
		assert new_res.metadata.relations[0].value == "Example article, https://example.com/article"
		assert len(new_res.metadata.awards) == 1
		assert new_res.metadata.awards[0].funding_agency_name == "National Science Foundation"
		assert new_res.metadata.awards[0].title == "Example Funding Award"
		assert new_res.metadata.awards[0].number == "NSF-123456"
		assert str(new_res.metadata.awards[0].funding_agency_url) == "https://www.nsf.gov/"
		assert len(new_res.metadata.creators) == 2
		assert new_res.metadata.creators[-1].name == "Doe, Jane"
		assert new_res.metadata.creators[-1].organization == "Example University"
		assert new_res.metadata.creators[-1].email == "jane.doe@example.com"
		assert len(new_res.metadata.contributors) == 1
		assert new_res.metadata.contributors[0].name == "Smith, Alex"
		assert new_res.metadata.contributors[0].organization == "Example Lab"
		assert new_res.metadata.contributors[0].email == "alex.smith@example.com"
		assert new_res.metadata.rights.statement == "Creative Commons Attribution 4.0 International"
		assert str(new_res.metadata.rights.url) == "https://creativecommons.org/licenses/by/4.0/"
		assert new_res.metadata.spatial_coverage.name == "Logan, Utah"
		assert new_res.metadata.spatial_coverage.northlimit == 41.7910
		assert new_res.metadata.spatial_coverage.eastlimit == -111.7664
		assert new_res.metadata.spatial_coverage.southlimit == 41.6732
		assert new_res.metadata.spatial_coverage.westlimit == -111.9079
		# check projection attribute does exist as the schema.org spatial coverage model has no matching fields
		# if we add the 'projection' field to the schema.org spatial coverage model,
		# we can update this assertion to check the value of the projection field.
		assert not hasattr(new_res.metadata.spatial_coverage, "projection")
		# assert new_res.metadata.spatial_coverage.projection == "WGS 84 EPSG:4326"

		assert hasattr(new_res.metadata.spatial_coverage, "type")
		assert new_res.metadata.spatial_coverage.type == "box"

		# check units attribute does exist as the schema.org spatial coverage model has no matching fields
		# if we add the 'units' field to the schema.org spatial coverage model,
		# we can update this assertion to check the value of the units field.
		assert not hasattr(new_res.metadata.spatial_coverage, "units")
		# assert new_res.metadata.spatial_coverage.units == "Decimal degrees"
		assert new_res.metadata.period_coverage.start.isoformat() == "2024-01-01T00:00:00"
		assert new_res.metadata.period_coverage.end.isoformat() == "2024-01-31T00:00:00"
		assert new_res.metadata.publisher is None

		# update using point spatial coverage
		new_res.metadata.spatial_coverage = PointCoverage(
			name="Logan, Utah",
			north=41.7910,
			east=-111.7664,
			projection="WGS 84 EPSG:4326",
			units="Decimal degrees",
		)
		new_res.save()
		assert new_res.metadata.spatial_coverage.name == "Logan, Utah"
		assert new_res.metadata.spatial_coverage.north == 41.7910
		assert new_res.metadata.spatial_coverage.east == -111.7664
		assert new_res.metadata.spatial_coverage.type == "point"
	finally:
		if new_res is not None:
			try:
				new_res.delete()
			except Exception:
				pass
