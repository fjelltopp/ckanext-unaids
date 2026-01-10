"""Tests for plugin.py."""
# encoding: utf-8
from unittest.mock import patch, call

from ckan.tests.helpers import call_action
from ckan.tests import factories
from ckan.plugins import toolkit
import pytest
from ckanext.unaids.plugin import (
    _update_resource_last_modified_date
)


def _resource_dict(resource_type='file'):
    if resource_type == 'file':
        return {
            'url_type': u'upload',
            'url': u'UTF-8-è file.csv',
            'lfs_prefix': u'prefix',
            'sha256': u'sha256',
            'size': 100,
        }
    elif resource_type == 'link':
        return {
            'url_type': u'',
            'url': u'http://example.com'
        }
    else:
        raise ValueError("Unsupported resource type %s", resource_type)


@pytest.fixture
def resource_with_file():
    return _resource_dict(resource_type='file')


@pytest.fixture
def resource_with_link():
    return _resource_dict(resource_type='link')


@pytest.fixture
def resource_with_updated_file():
    updated_resource = _resource_dict(resource_type='file')
    updated_resource['url'] = u'file2 è.csv'
    return updated_resource


@pytest.fixture
def resource_with_updated_link():
    updated_resource = _resource_dict(resource_type='link')
    updated_resource['url'] = u'http://example2.com'
    return updated_resource


@pytest.fixture
def resource_with_file_and_updated_metadata():
    updated_resource = _resource_dict(resource_type='file')
    updated_resource['description'] = u'updated-description'
    return updated_resource


@pytest.fixture
def resource_with_link_and_updated_metadata():
    updated_resource = _resource_dict(resource_type='link')
    updated_resource['description'] = u'updated-description'
    return updated_resource


@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids blob_storage scheming_datasets')
@pytest.mark.ckan_config('scheming.presets', 'ckanext.unaids:presets.json ckanext.scheming:presets.json')
@pytest.mark.usefixtures('with_plugins', 'clean_db')
class TestPlugin(object):
    '''Tests for the ckanext.example_iauthfunctions.plugin module.

    Specifically tests that overriding parent auth functions will cause
    child auth functions to use the overridden version.

    CKAN 2.11 Migration Notes:
    - Added clean_db fixture for test isolation
    - Added autouse setup_org fixture for user/org hierarchy
    - Added scheming.presets config for compatibility when running with other tests
    '''

    @pytest.fixture(autouse=True)
    def setup_org(self):
        """Create org and user for dataset creation in CKAN 2.11."""
        self.user = factories.User()
        self.org = factories.Organization(users=[{'name': self.user['id'], 'capacity': 'admin'}])

    def test_geojson_format_guessed_correctly(self):
        '''
        Test that the format of a geojson file is guessed correctly.
        '''
        dataset = factories.Dataset(owner_org=self.org['id'], user=self.user)
        resource = {
            'name': u'test',
            'url': u'file.geojson',
            'package_id': dataset['id'],
            'format': u'',
            'id': u''
        }
        context = {'user': self.user['name']}
        response = call_action('resource_create', context, **resource)
        response = call_action('package_show', context, id=dataset['id'])
        assert response['resources'][0]['format'] == 'GeoJSON'

    def test_blob_storage_validator_is_used_during_resource_actions(self):
        dataset = factories.Dataset(owner_org=self.org['id'], user=self.user)
        resource = {'name': 'test', 'package_id': dataset['id']}
        context = {'user': self.user['name']}
        # Patch in plugin.py where logic is imported from ckanext.unaids
        with patch('ckanext.unaids.plugin.logic.validate_resource_upload_fields') as mock:
            call_action('resource_create', context, **resource)
            assert mock.called


@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids blob_storage authz_service validation scheming_datasets')
@pytest.mark.ckan_config('scheming.dataset_schemas', 'ckanext.unaids.tests.test_scheming_schemas:validate_package.json')
@pytest.mark.ckan_config('scheming.presets', 'ckanext.unaids:presets.json ckanext.scheming:presets.json')
@pytest.mark.usefixtures('with_plugins', 'clean_db')
class TestValidatePackage(object):
    """Tests for validate_package functionality.

    CKAN 2.11 Migration Notes:
    - Changed to use regular 'dataset' type instead of 'validate-package' to avoid
      missing blueprint route for {package_type}_resource.download endpoint
    - The validate_package field on the resource is what triggers validation,
      not the dataset type, so this change doesn't affect test functionality
    - Added org/user fixtures for dataset creation
    - CKAN 2.11 activity plugin requires user context in call_action for resource operations
    """

    @pytest.fixture
    def validate_package_user(self):
        """Create a user for validation testing."""
        return factories.User()

    @pytest.fixture
    def validate_package_resource(self, validate_package_user):
        """Create a dataset with a resource for validation testing."""
        user = validate_package_user
        org = factories.Organization(users=[{'name': user['id'], 'capacity': 'admin'}])
        dataset = factories.Dataset(
            owner_org=org['id'],
            user=user
        )
        resource = {
            'package_id': dataset["id"],
            'url_type': 'upload',
            'url': 'test.csv',
            'lfs_prefix': 'prefix',
            'sha256': 'acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79',
            'size': 100,
            'validate_package': True
        }
        # CKAN 2.11: Activity plugin requires user context
        resource["id"] = call_action(
            'resource_create', {'user': user['name']}, **resource
        )["id"]
        return resource

    def test_validate_package(self, validate_package_resource, validate_package_user):

        def return_value(*args, **kwargs):
            return toolkit.get_action(*args, **kwargs)

        with patch('ckanext.unaids.plugin.toolkit.get_action', return_value=return_value) as mock:
            call_action(
                'resource_update', {'user': validate_package_user['name']},
                **validate_package_resource
            )
            mock.assert_any_call('resource_validation_run_batch')

    def test_metadata_change_does_not_validate_package(
            self, validate_package_resource, validate_package_user):
        del validate_package_resource['url']

        def return_value(*args, **kwargs):
            return toolkit.get_action(*args, **kwargs)

        with patch('ckanext.unaids.plugin.toolkit.get_action', return_value=return_value) as mock:
            call_action(
                'resource_patch', {'user': validate_package_user['name']},
                **validate_package_resource
            )
            assert call('resource_validation_run_batch') not in mock.mock_calls


class TestResourceLastModified(object):
    '''Tests for the ckanext.plugin._update_resource_last_modified_date module.

    Make sure we are setting the last_modified to the resource dict
    whenever a resource is created or edited.
    '''

    def test_null_to_file_should_update_last_modified_datetime(self, resource_with_file):
        _update_resource_last_modified_date(resource_with_file)
        assert 'last_modified' in resource_with_file

    def test_file_to_null_should_not_update_last_modified_datetime(self, resource_with_file):
        null_resource = {}
        _update_resource_last_modified_date(
            null_resource, current=resource_with_file
        )
        assert 'last_modified' not in resource_with_file

    def test_file_to_file_should_update_last_modified_datetime(
            self, resource_with_file, resource_with_updated_file):
        _update_resource_last_modified_date(
            resource_with_updated_file, current=resource_with_file
        )
        assert 'last_modified' in resource_with_updated_file

    def test_file_to_link_should_update_last_modified_datetime(
            self, resource_with_file, resource_with_link):
        _update_resource_last_modified_date(
            resource_with_link, current=resource_with_file
        )
        assert 'last_modified' in resource_with_link

    def test_changing_metadata_in_file_should_not_update_last_modified_datetime(
            self, resource_with_file, resource_with_file_and_updated_metadata):
        _update_resource_last_modified_date(
            resource_with_file_and_updated_metadata, current=resource_with_file
        )
        assert 'last_modified' not in resource_with_file_and_updated_metadata

    def test_null_to_link_should_update_last_modified_datetime(self, resource_with_link):
        _update_resource_last_modified_date(resource_with_link)
        assert 'last_modified' in resource_with_link

    def test_link_to_null_should_not_update_last_modified_datetime(self, resource_with_link):
        null_resource = {}
        _update_resource_last_modified_date(
            null_resource, current=resource_with_link
        )
        assert 'last_modified' not in resource_with_link

    def test_link_to_link_should_update_last_modified_datetime(
            self, resource_with_link, resource_with_updated_link):
        _update_resource_last_modified_date(
            resource_with_updated_link, current=resource_with_link
        )
        assert 'last_modified' in resource_with_updated_link

    def test_link_to_file_should_update_last_modified_datetime(
            self, resource_with_file, resource_with_link):
        _update_resource_last_modified_date(
            resource_with_file, current=resource_with_link
        )
        assert 'last_modified' in resource_with_file

    def test_changing_metadata_in_link_should_not_update_last_modified_datetime(
            self, resource_with_link, resource_with_link_and_updated_metadata):
        _update_resource_last_modified_date(
            resource_with_link_and_updated_metadata, current=resource_with_link
        )
        assert 'last_modified' not in resource_with_link_and_updated_metadata
