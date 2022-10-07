"""Tests for plugin.py."""
import logging
import pytest
import ckan.model
import ckan.plugins
from ckanext.unaids.tests.factories import User

log = logging.getLogger(__name__)


@pytest.mark.ckan_config('ckan.plugins', 'unaids pages')
@pytest.mark.usefixtures('with_plugins')
class TestValidateUserProfileBlueprint(object):

    def test_validate_user_profile_blueprint_intercepts_incomplete(self, app):
        ckan.plugins.unload('unaids')
        user = User()
        ckan.plugins.load('unaids')
        user_response = app.get(
            url=ckan.plugins.toolkit.url_for(
                'validate_user_profile.check_user_affiliation'
            ),
            headers={
                'Authorization': user['apikey']
            },
            follow_redirects=False,
        )
        assert 'user/edit' in user_response.location

    def test_validate_user_profile_blueprint_does_not_intercept_complete(self, app):
        user = User(
            job_title='Data Scientist',
            affiliation='Fjelltopp',
        )
        user_response = app.get(
            url=ckan.plugins.toolkit.url_for(
                'validate_user_profile.check_user_affiliation'
            ),
            headers={
                'Authorization': user['apikey']
            },
            follow_redirects=False,
        )
        assert '/dashboard/' in user_response.location

    def test_annonymous_access_to_index_page(self, app):
        index_response = app.get(
            '/',
            follow_redirects=False
        )
        assert index_response.status_code == 200
