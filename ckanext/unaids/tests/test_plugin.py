"""Tests for plugin.py."""
# encoding: utf-8

from ckan.tests.helpers import call_action
from ckan.tests import factories
import ckan.tests.helpers as helpers


class TestPlugin(helpers.FunctionalTestBase):
    '''Tests for the ckanext.example_iauthfunctions.plugin module.

    Specifically tests that overriding parent auth functions will cause
    child auth functions to use the overridden version.
    '''
    _load_plugins = ['unaids']

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