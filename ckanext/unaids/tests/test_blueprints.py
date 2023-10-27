"""Tests for plugin.py."""
import logging
import pytest
import ckan.plugins.toolkit as toolkit
import pandas
from numpy import nan
from io import StringIO

log = logging.getLogger(__name__)


@pytest.mark.ckan_config('ckan.plugins', 'ytp_request unaids pages')
@pytest.mark.usefixtures('with_plugins')
class TestValidateUserProfileBlueprint(object):
    def test_annonymous_access_to_index_page(self, app):
        index_response = app.get("/", follow_redirects=False)
        assert index_response.status_code == 200


@pytest.fixture
def test_org_download(app, test_organization):
    url = toolkit.url_for(
        'members_list.org_member_download',
        group_id=test_organization['name']
    )
    org_admin_username = test_organization['users'][0]['name']
    return app.get(url, extra_environ={'REMOTE_USER': org_admin_username})


@pytest.mark.ckan_config("ckan.plugins", "ytp_request unaids pages")
@pytest.mark.usefixtures("with_plugins")
class TestMemberLists(object):
    def test_org_member_download_200_ok(self, test_org_download):
        assert test_org_download.status_code == 200

    def test_org_member_download_expected_columns(self, test_org_download):
        df = pandas.read_csv(StringIO(test_org_download.body))
        expected_columns = {
            "Username",
            "Email",
            "Full Name",
            "Affiliation",
            "Job Title",
            "ADR Org",
            "ADR Org Role"
        }
        assert set(df.columns) == expected_columns

    def test_org_member_download_expected_emails(self, test_org_download):
        df = pandas.read_csv(StringIO(test_org_download.body))
        expected_emails = {
            "admin@ckan.org",
            "editor@ckan.org",
            "member@ckan.org",
            nan
        }
        assert set(df['Email']) == expected_emails

    def test_org_member_download_403(self, app, test_organization):
        url = toolkit.url_for(
            'members_list.org_member_download',
            group_id=test_organization['name']
        )
        org_editor_username = test_organization['users'][1]['name']
        response = app.get(url, extra_environ={'REMOTE_USER': org_editor_username})
        assert response.status_code == 403

    def test_org_member_download_404(self, app, test_organization):
        url = toolkit.url_for(
            'members_list.org_member_download',
            group_id="bad-name"
        )
        org_editor_username = test_organization['users'][1]['name']
        response = app.get(url, extra_environ={'REMOTE_USER': org_editor_username})
        assert response.status_code == 404

    def test_org_member_download_anonymous_access(self, app, test_organization):
        url = toolkit.url_for(
            'members_list.org_member_download',
            group_id="bad-name"
        )
        response = app.get(url)
        assert response.status_code == 403
