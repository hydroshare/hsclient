from hsclient.json_models import ResourcePreview


def test_resource_preview_authors_field_default_is_empty_list():
    """verify all `authors` fields are instantiated with [] values."""
    test_data_dict = {"authors": None}
    test_data_json = '{"authors": null}'

    base_case = ResourcePreview()
    from_kwargs = ResourcePreview(**test_data_dict)
    from_dict = ResourcePreview.parse_obj(test_data_dict)
    from_json = ResourcePreview.parse_raw(test_data_json)

    assert all([x.authors == [] for x in [base_case, from_kwargs, from_dict, from_json]])


def test_resource_preview_authors_field_default_is_None_list():
    """verify all `authors` fields are instantiated with [] values."""
    test_data_dict = {"authors": [None]}
    test_data_json = '{"authors": [null]}'

    base_case = ResourcePreview()
    from_kwargs = ResourcePreview(**test_data_dict)
    from_dict = ResourcePreview.parse_obj(test_data_dict)
    from_json = ResourcePreview.parse_raw(test_data_json)

    assert all([x.authors == [] for x in [base_case, from_kwargs, from_dict, from_json]])
