from hs_rdf.implementations.hydroshare import HydroShare


def test_resource():
    hs = HydroShare('sblack', 'password')
    resource = hs.create()

    assert 0 == len(resource.metadata.subjects)

    resource.metadata.subjects = ['sub1', 'sub2']
    resource.metadata.title = "resource test"

    resource.save()
    resource.refresh()

    assert 'resource test' == resource.metadata.title
    assert 2 == len(resource.metadata.subjects)
