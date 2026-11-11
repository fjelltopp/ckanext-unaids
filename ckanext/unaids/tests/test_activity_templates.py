# -*- coding: utf-8 -*-
"""The unaids templates that sit on top of the activity extension's templates.

CKAN 2.11 moved activity streams into the ``activity`` extension. ``unaids`` is
listed before ``activity`` in ``ckan.plugins``, so our template wins whenever
both have a template with the same name. These tests check the pages where the
two extensions meet.
"""

import pytest
from bs4 import BeautifulSoup
from ckan.lib.helpers import url_for
from ckan.tests import factories
from ckan.tests.factories import User
from ckanext.unaids.tests import create_dataset_with_releases

PLUGINS = 'unaids activity ytp_request blob_storage versions pages scheming_datasets'


def tab_labels(response):
    soup = BeautifulSoup(response.body, 'html.parser')
    return [a.get_text(strip=True) for a in soup.select('.nav-tabs a')]


@pytest.mark.usefixtures('with_plugins')
@pytest.mark.ckan_config('ckan.plugins', PLUGINS)
class TestNavigationTabs(object):

    def test_dataset_page_has_dataset_activity_and_releases_tabs(self, app):
        user = User()
        dataset, _ = create_dataset_with_releases(user)
        response = app.get(
            url_for('dataset.read', id=dataset['name']),
            extra_environ={'REMOTE_USER': user['name']},
        )
        assert tab_labels(response) == ['Dataset', 'Activity Stream', 'Releases']

    def test_organization_page_has_activity_tab(self, app):
        user = User()
        org = factories.Organization(user=user)
        response = app.get(
            url_for('organization.about', id=org['name']),
            extra_environ={'REMOTE_USER': user['name']},
        )
        assert 'Activity Stream' in tab_labels(response)


@pytest.mark.usefixtures('with_plugins')
@pytest.mark.ckan_config('ckan.plugins', PLUGINS)
class TestDatasetActivityStream(object):

    def _stream(self, app, user, dataset, **params):
        response = app.get(
            url_for('activity.package_activity', id=dataset['name'], **params),
            extra_environ={'REMOTE_USER': user['name']},
        )
        assert response.status_code == 200
        return response.body

    def test_releases_are_named_in_the_stream(self, app):
        user = User()
        dataset, releases = create_dataset_with_releases(user)
        body = self._stream(app, user, dataset)
        for release in releases:
            assert release['name'] in body

    def test_activities_without_a_release_offer_add_release(self, app):
        user = User()
        dataset, _ = create_dataset_with_releases(user)
        # create_dataset_with_releases leaves one activity after the last release
        assert 'Add Release' in self._stream(app, user, dataset)

    def test_release_links_are_hidden_from_users_who_cannot_create_releases(self, app):
        owner, outsider = User(), User()
        dataset, releases = create_dataset_with_releases(owner)
        body = self._stream(app, outsider, dataset)
        assert 'Add Release' not in body
        assert releases[0]['name'] not in body

    def test_stream_links_to_the_old_version_and_its_changes(self, app):
        user = User()
        dataset, _ = create_dataset_with_releases(user)
        body = self._stream(app, user, dataset)
        assert '/history/' in body
        assert '/changes/' in body

    def test_create_release_banner(self, app):
        user = User()
        dataset, _ = create_dataset_with_releases(user)
        body = self._stream(app, user, dataset, create_release=True)
        assert 'Use the "Add Release" button' in body
        assert 'Use the "Add Release" button' not in self._stream(app, user, dataset)


@pytest.mark.usefixtures('with_plugins')
@pytest.mark.ckan_config('ckan.plugins', PLUGINS)
class TestEmailNotificationsSetting(object):

    def _edit_page(self, app, user):
        response = app.get(
            url_for('user.edit', id=user['name']),
            extra_environ={'REMOTE_USER': user['name']},
        )
        return BeautifulSoup(response.body, 'html.parser')

    @pytest.mark.ckan_config('ckan.activity_streams_email_notifications', 'true')
    def test_checkbox_is_shown_when_notifications_are_enabled(self, app):
        user = User()
        checkbox = self._edit_page(app, user).find(id='field-activity-streams-email-notifications')
        assert checkbox is not None
        assert not checkbox.has_attr('checked')

    @pytest.mark.ckan_config('ckan.activity_streams_email_notifications', 'true')
    def test_checkbox_reflects_the_saved_setting(self, app):
        user = User(activity_streams_email_notifications=True)
        checkbox = self._edit_page(app, user).find(id='field-activity-streams-email-notifications')
        assert checkbox.has_attr('checked')

    @pytest.mark.ckan_config('ckan.activity_streams_email_notifications', 'false')
    def test_checkbox_is_hidden_when_notifications_are_disabled(self, app):
        user = User()
        assert self._edit_page(app, user).find(id='field-activity-streams-email-notifications') is None
