import pytest

from ckan.plugins import toolkit
from ckan.tests import factories
from ckanext.unaids import logic


@pytest.mark.ckan_config('ckan.plugins', 'unaids authz_service blob_storage')
@pytest.mark.usefixtures('with_plugins')
@pytest.mark.parametrize(
    "lfs_prefix,sha256,size,valid",
    [
        ("fjelltopp/my-dataset", "acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79", 100, True),
        (None, None, None, True),
        ("", "", "", True),
        (None, "", "", False),
        ("fjelltopp/my-dataset", "acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79", None, False),
        (None, None, 100, False),
        ("fjelltopp/my-dataset", "", 100, False),
        ("fjelltopp/my-dataset", None, 100, False),
        ("", "acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79", 100, False),
        ("", "invalid_sha256", 100, False),
        ("", "acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79", 100, False),
        (None, "acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79", 100, False),
        ("fjelltopp/my-dataset", "", 100, False)
    ], ids=[
        "validates if all upload fields correct",
        "validates if no upload fields present",
        "validates if all fields are present but empty",
        "fails if some fields missing and others set to empty string",
        "fails if size None",
        "fails if only size present",
        "fails if sha256 empty string",
        "fails if sha256 None",
        "fails if only sha256 present",
        "fails if invalid sha256",
        "fails if lfs_prefix empty string",
        "fails if lfs_prefix None",
        "fails if only lfs_prefix present"
    ])
def test_validate_resource_upload_fields(lfs_prefix, sha256, size, valid):
    context = {}
    resource_dict = {}
    for key, val in [('sha256', sha256), ('lfs_prefix', lfs_prefix), ('size', size)]:
        if val is not None:
            resource_dict[key] = val
    if not valid:
        with pytest.raises(toolkit.ValidationError):
            logic.validate_resource_upload_fields(context, resource_dict)
    else:
        logic.validate_resource_upload_fields(context, resource_dict)


@pytest.mark.ckan_config('ckan.plugins', 'unaids authz_service blob_storage')
@pytest.mark.usefixtures('with_plugins')
def test_update_filename_in_resource_url():
    actual_filename = "TeSt.CSV"
    resource = factories.Resource(url_type="upload",
                                  url=actual_filename,
                                  sha256="cc71500070cf26cd6e8eab7c9eec3a937be957d144f445ad24003157e2bd0919",
                                  lfs_prefix="lfs/prefix",
                                  size=500
                                  )
    assert resource['url'].endswith(actual_filename)


class TestAutoPopulateDataDictionaries():

    def test_no_schema(self, mocker):
        context = {}
        dataset = factories.Dataset()
        resource = factories.Resource(package_id=dataset['id'])
        mock_load_json_schema = mocker.patch(
            'ckanext.unaids.logic.validation_load_json_schema',
            return_value=None
        )
        logic.auto_populate_data_dictionary(context, resource)
        mock_load_json_schema.assert_not_called()

    def test_missing_schema(self, mocker):
        context = {}
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            schema='test_schema'
        )
        mock_load_json_schema = mocker.patch(
            'ckanext.unaids.logic.validation_load_json_schema',
            return_value=None
        )
        with pytest.raises(toolkit.ObjectNotFound):
            logic.auto_populate_data_dictionary(context, resource)
        mock_load_json_schema.assert_called_once_with(u'test_schema')

    def test_simple_schema(self, mocker):
        context = {}
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            schema='test_schema'
        )
        mock_load_json_schema = mocker.patch(
            'ckanext.unaids.logic.validation_load_json_schema',
            return_value={
                "title": "UNAIDS ART Programme Input",
                "fields": [
                    {
                        "name": "area_id",
                        "title": "Area ID",
                        "description": "An area_id from the agreed hierarchy.",
                        "type": "string",
                        "constraints": {
                            "required": True
                        }
                    }, {
                        "name": "area_name",
                        "title": "Area Name",
                        "description": "Area name for area_id (optional).",
                        "type": "string"
                    }
                ]
            }
        )
        mock_datastore_search = mocker.Mock(
            return_value={
                'fields': [
                    {'id': '_id', 'type': 'numeric'},
                    {'id': 'area_id', 'type': 'numeric'},
                    {'id': 'area_name', 'type': 'text', 'info': {'notes': 'Existing notes'}},
                ]
            }
        )
        mock_action = mocker.Mock()

        def side_effect(action_name):

            if action_name == 'datastore_search':
                return mock_datastore_search

            else:
                return mock_action

        mock_get_action = mocker.patch(
            'ckanext.unaids.logic.toolkit.get_action',
            side_effect=side_effect
        )

        logic.auto_populate_data_dictionary(context, resource)
        mock_load_json_schema.assert_called_once_with(u'test_schema')
        mock_get_action.assert_called_with('datastore_create')
        mock_action.assert_called_with(context, {
            u'resource_id': resource[u'id'],
            u'force': True,
            u'fields': [
                {
                    u'id': u'area_id',
                    u'type': u'numeric',
                    u'info': {
                        u'label': u'Area ID',
                        u'notes': u'An area_id from the agreed hierarchy.'
                    }
                }, {
                    u'id': u'area_name',
                    u'type': u'text',
                    u'info': {
                        u'notes': u'Existing notes'
                    }
                }
            ]
        })
