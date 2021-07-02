"""Tests for plugin.py."""
# encoding: utf-8

from ckan.tests.helpers import call_action
from ckan.tests import factories
import pytest
from ckanext.unaids.plugin import (
    _update_resource_last_modified_date
)


@pytest.mark.ckan_config('ckan.plugins', 'unaids')
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
            'name': 'test',
            'url': 'file.geojson',
            'package_id': dataset['id'],
            'format': '',
            'id': ''
        }
        response = call_action('resource_create', {}, **resource)
        response = call_action('package_show', {}, id=dataset['id'])
        assert response['resources'][0]['format'] == 'GeoJSON'


class TestResourceLastModified(object):
    '''Tests for the ckanext.plugin._update_resource_last_modified_date module.

    Make sure we are setting the last_modified to the resource dict
    whenever a resource is created or edited.
    '''

    URL_TYPE_FILE_UPLOAD = 'upload'
    URL_TYPE_LINK = ''

    def test_resource(self, url_type):
        resource_dict = {'url_type': url_type}
        if url_type == self.URL_TYPE_FILE_UPLOAD:
            resource_dict.update({
                'url': 'file.csv',
                'lfs_prefix': 'prefix123',
                'sha256': 'sha256',
                'size': 100,
            })
        elif url_type == self.URL_TYPE_LINK:
            resource_dict.update({
                'url': 'http://example.com'
            })
        return resource_dict

    def test_null_to_file(self):
        resource = self.test_resource(self.URL_TYPE_FILE_UPLOAD)
        _update_resource_last_modified_date(resource=resource)
        assert 'last_modified' in resource

    def test_file_to_null(self):
        resource = self.test_resource(self.URL_TYPE_FILE_UPLOAD)
        _update_resource_last_modified_date({}, resource)
        assert 'last_modified' not in resource

    def test_file_to_url(self):
        current = self.test_resource(self.URL_TYPE_FILE_UPLOAD)
        resource = self.test_resource(self.URL_TYPE_LINK)
        _update_resource_last_modified_date(resource, current)
        assert 'last_modified' in resource

    def test_null_to_url(self):
        resource = self.test_resource(self.URL_TYPE_LINK)
        _update_resource_last_modified_date(resource=resource)
        assert 'last_modified' in resource

    def test_url_to_null(self):
        resource = self.test_resource(self.URL_TYPE_LINK)
        _update_resource_last_modified_date({}, resource)
        assert 'last_modified' not in resource

    def test_url_to_file(self):
        current = self.test_resource(self.URL_TYPE_LINK)
        resource = self.test_resource(self.URL_TYPE_FILE_UPLOAD)
        _update_resource_last_modified_date(resource, current)
        assert 'last_modified' in resource
