"""Tests for plugin.py."""
# encoding: utf-8

import ckan.plugins
from ckan.tests.helpers import call_action, reset_db
from ckan.tests import factories
import ckan.tests.helpers as helpers
from ckanext.validation.model import create_tables, tables_exist
import logging


class TestPlugin(helpers.FunctionalTestBase):
    '''Tests for the ckanext.example_iauthfunctions.plugin module.

    Specifically tests that overriding parent auth functions will cause
    child auth functions to use the overridden version.
    '''
    def setup(self):
        reset_db()
        if not tables_exist():
            create_tables()
        self.app = self._get_test_app()
        ckan.plugins.load('unaids')

    def teardown(self):
        '''
        Nose runs this method once after all the test methods in our class
        have been run.
        '''
        # We have to unload the plugin we loaded, so it doesn't affect any
        # tests that run after ours.
        ckan.plugins.unload('unaids')

    def test_geojson_format_guessed_correctly(self):
        '''
        Test that the format of a geojson file is guessed correctly.
        '''
        logging.warning('RUNNING Test')
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
