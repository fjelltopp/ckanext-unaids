"""Tests for plugin.py."""
# encoding: utf-8

# from nose.tools import assert_raises
import ckan.model as model
import ckan.plugins
# import ckan.tests.factories as factories
# import ckan.logic as logic


class TestYTPRequestsPlugin(object):
    '''Tests for the ckanext.example_iauthfunctions.plugin module.

    Specifically tests that overriding parent auth functions will cause
    child auth functions to use the overridden version.
    '''
    @classmethod
    def setup_class(cls):
        '''Nose runs this method once to setup our test class.'''
        # Test code should use CKAN's plugins.load() function to load plugins
        # to be tested.
        ckan.plugins.load('ytp_request')

    def teardown(self):
        '''Nose runs this method after each test method in our test class.'''
        # Rebuild CKAN's database after each test method, so that each test
        # method runs with a clean slate.
        model.repo.rebuild_db()

    @classmethod
    def teardown_class(cls):
        '''
        Nose runs this method once after all the test methods in our class
        have been run.
        '''
        # We have to unload the plugin we loaded, so it doesn't affect any
        # tests that run after ours.
        ckan.plugins.unload('ytp_request')

    def sample_test(self):
        '''
        Placeholder test.
        '''
        pass
