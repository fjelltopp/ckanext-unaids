"""Tests for plugin.py."""
import logging
import mock
import pytest
import ckan.model
import ckan.plugins
from ckan.tests import factories
from ckanext.unaids.tests import get_context
from ckanext.unaids.blueprints.user_affiliation import get_route_to_intercept

log = logging.getLogger(__name__)


@pytest.mark.ckan_config('ckan.plugins', 'unaids')
@pytest.mark.usefixtures('with_plugins')
class TestUserAffiliationBlueprint(object):
    
    # @mock.patch('ckanext.unaids.blueprints.user_affiliation.h.flash_error')
    def test_user_affiliation_blueprint_intercepts(self, app):
        ckan.plugins.unload('unaids')
        user = factories.User()
        ckan.plugins.load('unaids')
        url_after_login = get_route_to_intercept()
        print(url_after_login)
        user_response = app.get(url_after_login, headers={
            'Authorization': user['apikey']
        })
