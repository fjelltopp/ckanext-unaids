"""Tests for plugin.py."""
# encoding: utf-8
from mock import patch

from ckan.tests.helpers import call_action
from ckan.tests import factories
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


@pytest.mark.ckan_config('ckan.plugins', 'unaids blob_storage')
@pytest.mark.usefixtures('with_plugins')
class TestPlugin(object):
    '''Tests for the ckanext.example_iauthfunctions.plugin module.

    Specifically tests that overriding parent auth functions will cause
    child auth functions to use the overridden version.
    '''

    def test_geojson_format_guessed_correctly(self):
        '''
        Test that the format of a geojson file is guessed correctly.
        '''
        dataset = factories.Dataset()
        resource = {
            'name': u'test',
            'url': u'file.geojson',
            'package_id': dataset['id'],
            'format': u'',
            'id': u''
        }
        response = call_action('resource_create', {}, **resource)
        response = call_action('package_show', {}, id=dataset['id'])
        assert response['resources'][0]['format'] == 'GeoJSON'

    def test_blob_storage_validator_is_used_during_resource_actions(self):
        dataset = factories.Dataset()
        resource = {'name': 'test', 'package_id': dataset['id']}
        context = {}
        with patch('ckanext.unaids.logic.validate_resource_upload_fields') as mock:
            call_action('resource_create', context, **resource)
            assert mock.called


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
