"""Tests for plugin.py."""
import logging
import pytest
import ckan.model
import ckan.plugins
from ckanext.unaids.tests.factories import User
from ckanext.unaids.blueprints.validate_user_profile import get_route_to_intercept

log = logging.getLogger(__name__)


@pytest.mark.ckan_config('ckan.plugins', 'unaids')
@pytest.mark.usefixtures('with_plugins')
class TestValidateUserProfileBlueprint(object):

    def test_validate_user_profile_blueprint_intercepts(self, app):
        ckan.plugins.unload('unaids')
        user = User()
        ckan.plugins.load('unaids')
        url_after_login = get_route_to_intercept()
        user_response = app.get(url_after_login, headers={
            'Authorization': user['apikey']
        }, follow_redirects=False)
        assert 'user/edit' in user_response.location
