"""Tests for plugin.py."""
# encoding: utf-8

from ckan.tests.helpers import call_action
from ckan.tests import factories
import pytest
import logging
from pprint import pformat

log = logging.getLogger(__name__)


@pytest.mark.ckan_config('ckan.plugins', 'unaids')
@pytest.mark.usefixtures('with_plugins')
class TestGetTableSchema(object):

    def test_schema_returned_successfully(self, ):
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            schema='non_existant_schema'
        )
        log.debug("Resource dict: {}".format(pformat(resource)))
        response = call_action('get_table_schema', {}, resource_id=resource['id'])
        log.debug("Table schema: {}".format(pformat(response)))
        assert response == {}

    def test_empty_dict_returned_for_no_schema(self, ):
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            schema='non_existant_schema'
        )
        log.debug("Resource dict: {}".format(pformat(resource)))
        response = call_action('get_table_schema', {}, resource_id=resource['id'])
        log.debug("Table schema: {}".format(pformat(response)))
        assert response == {}
