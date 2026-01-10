"""Tests for plugin.py."""
import logging
import pytest
import ckan.plugins.toolkit as toolkit
import pandas
from numpy import nan
from io import StringIO

log = logging.getLogger(__name__)


@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids pages')
@pytest.mark.usefixtures('with_plugins')
class TestValidateUserProfileBlueprint(object):
    def test_annonymous_access_to_index_page(self, app):
        index_response = app.get("/", follow_redirects=False)
        assert index_response.status_code == 200


@pytest.mark.ckan_config("ckan.plugins", "activity ytp_request unaids pages")
@pytest.mark.usefixtures("with_plugins")
class TestMemberLists(object):
    """Tests for the members list download blueprint.

    CKAN 2.11 Migration Notes:
    - Uses explicit user fixtures (org_admin, org_editor) instead of relying on
      test_organization['users'] ordering which may not be preserved.
    - Email tests check for actual factory-generated emails (domain: ckan.example.com)
      rather than hardcoded values.
    """

    @pytest.fixture
    def test_org_download(self, app, test_organization, org_admin):
        """Download members list as org admin."""
        url = toolkit.url_for(
            'members_list.org_member_download',
            group_id=test_organization['name']
        )
        return app.get(url, extra_environ={'REMOTE_USER': org_admin['name']})

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

    def test_org_member_download_expected_emails(
        self, test_org_download, org_admin, org_editor, org_member
    ):
        """Check that member emails are present in the download.

        CKAN 2.11: factories.User generates emails with domain ckan.example.com,
        not hardcoded values like admin@ckan.org.
        """
        df = pandas.read_csv(StringIO(test_org_download.body))
        expected_emails = {
            org_admin['email'],
            org_editor['email'],
            org_member['email'],
        }
        # The site user may have NaN email
        actual_emails = set(df['Email'].dropna())
        assert actual_emails == expected_emails

    def test_org_member_download_403(self, app, test_organization, org_editor):
        """Editors should not be able to download member lists."""
        url = toolkit.url_for(
            'members_list.org_member_download',
            group_id=test_organization['name']
        )
        response = app.get(url, extra_environ={'REMOTE_USER': org_editor['name']})
        assert response.status_code == 403

    def test_org_member_download_404(self, app, org_editor):
        """Non-existent org should return 404."""
        url = toolkit.url_for(
            'members_list.org_member_download',
            group_id="bad-name"
        )
        response = app.get(url, extra_environ={'REMOTE_USER': org_editor['name']})
        assert response.status_code == 404

    def test_org_member_download_anonymous_access(self, app, test_organization):
        """Anonymous users should get 403."""
        url = toolkit.url_for(
            'members_list.org_member_download',
            group_id=test_organization['name']
        )
        response = app.get(url)
        assert response.status_code == 403
