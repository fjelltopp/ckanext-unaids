# -*- coding: utf-8 -*-

import pytest
from bs4 import BeautifulSoup
from ckan.lib.helpers import url_for
import ckan.tests.factories as factories
from ckan.plugins import toolkit
from ckanext.versions.logic.dataset_version_action import (
    dataset_version_create, dataset_version_list
)
from ckanext.versions.tests.fixtures import versions_setup  # noqa
from ckanext.versions.tests import get_context
from nose.tools import assert_equals, assert_in, assert_not_in
from ckanext.unaids.blueprints.unaids_dataset_releases import SOMETHING_WENT_WRONG_ERROR


def create_dataset_with_releases(user, number_of_releases=5):
    org = factories.Organization(user=user)
    dataset = factories.Dataset(user=user, owner_org=org['id'])
    releases = []
    for x in range(number_of_releases):
        activities = toolkit.get_action('package_activity_list')(
            get_context(user),
            {'id': dataset['id']}
        )
        releases.append(dataset_version_create(
            get_context(user),
            {
                'dataset_id': dataset['id'],
                'activity_id': activities[0]['id'],
                'name': 'release-{}'.format(x),
                'notes': 'Test Notes'
            }
        ))
        toolkit.get_action('package_patch')(
            get_context(user),
            {
                'id': dataset['id'],
                'title': 'updated-title-{}'.format(x)
            }
        )
    return dataset, releases


def get_listview(app, user, dataset):
    return app.get(
        url=url_for(
            'unaids_dataset_releases.list_releases',
            dataset_type=dataset['type'],
            dataset_id=dataset['id']
        ),
        extra_environ={'REMOTE_USER': user['name']}
    )


def assert_releases_are_exactly(user, dataset_id, expected_releases):
    # TODO: better function name?
    releases = dataset_version_list(
        get_context(user), {'dataset_id': dataset_id}
    )
    assert_equals(len(releases), len(expected_releases))
    assert_equals(
        sorted([x['name'] for x in releases]),
        sorted([x['name'] for x in expected_releases])
    )


@pytest.mark.usefixtures('clean_db', 'versions_setup')
@pytest.mark.usefixtures('with_plugins')
@pytest.mark.ckan_config('ckan.plugins', 'unaids blob_storage versions')
class TestDatasetReleaseCreateAndEdit(object):

    def _create_or_edit(self, app, user, dataset, release):
        response = app.post(
            url=url_for(
                'unaids_dataset_releases.release_view',
                dataset_type=dataset['type'],
                dataset_id=dataset['id'],
                release_id=release.get('id')
            ),
            data=release,
            extra_environ={'REMOTE_USER': user['name']}
        )
        assert response.status_code == 200
        soup = BeautifulSoup(response.body)
        flash_messages = soup.find('div', {'class': 'flash-messages'}).text
        return flash_messages

    def test_create_with_valid_user(self, app):
        user = factories.User()
        dataset, releases = create_dataset_with_releases(user)
        release = {'name': 'my-new-release', 'notes': 'example'}
        flash_message = self._create_or_edit(app, user, dataset, release)
        assert_in('Release {} added'.format(release['name']), flash_message)
        assert_releases_are_exactly(user, dataset['id'], releases + [release])

    def test_create_with_invalid_user(self, app):
        user_1, user_2 = factories.User(), factories.User()
        dataset, releases = create_dataset_with_releases(user_1)
        release = {'name': 'my-new-release', 'notes': 'example'}
        flash_message = self._create_or_edit(
            app, user_2, dataset, release
        )
        assert_in(SOMETHING_WENT_WRONG_ERROR, flash_message)
        assert_releases_are_exactly(user_1, dataset['id'], releases)

    def test_edit_with_valid_user(self, app):
        user = factories.User()
        dataset, releases = create_dataset_with_releases(user)
        updated_release = releases[0]
        updated_release['name'] = 'updated-release-name'
        flash_message = self._create_or_edit(
            app, user, dataset, updated_release)
        assert_in('Release {} updated'.format(
            updated_release['name']), flash_message)
        assert_releases_are_exactly(user, dataset['id'], releases)

    def test_edit_with_invalid_user(self, app):
        user_1, user_2 = factories.User(), factories.User()
        dataset, releases = create_dataset_with_releases(user_1)
        updated_release = releases[0].copy()
        updated_release['name'] = 'updated-release-name'
        flash_message = self._create_or_edit(
            app, user_2, dataset, updated_release
        )
        assert_in(SOMETHING_WENT_WRONG_ERROR, flash_message)
        assert_releases_are_exactly(user_1, dataset['id'], releases)


@pytest.mark.usefixtures('clean_db', 'versions_setup')
@pytest.mark.usefixtures('with_plugins')
@pytest.mark.ckan_config('ckan.plugins', 'unaids blob_storage versions')
class TestDatasetReleaseDelete(object):

    def _delete(self, app, user, dataset, release):
        response = app.post(
            url=url_for(
                'unaids_dataset_releases.release_delete',
                dataset_type=dataset['type'],
                dataset_id=dataset['id'],
                release_id=release['id']
            ),
            extra_environ={'REMOTE_USER': user['name']}
        )
        assert response.status_code == 200
        soup = BeautifulSoup(response.body)
        flash_messages = soup.find('div', {'class': 'flash-messages'}).text
        return flash_messages

    def test_delete_with_valid_user(self, app):
        user = factories.User()
        dataset, releases = create_dataset_with_releases(user)
        deleted_release = releases.pop()
        flash_message = self._delete(app, user, dataset, deleted_release)
        assert_in(
            'Release {} deleted'.format(deleted_release['name']),
            flash_message
        )
        assert_releases_are_exactly(user, dataset['id'], releases)

    def test_delete_with_invalid_user(self, app):
        user_1, user_2 = factories.User(), factories.User()
        dataset, releases = create_dataset_with_releases(user_1)
        deleted_release = releases[0]
        flash_message = self._delete(
            app, user_2, dataset, deleted_release
        )
        assert_in(SOMETHING_WENT_WRONG_ERROR, flash_message)
        assert_releases_are_exactly(user_1, dataset['id'], releases)


@pytest.mark.usefixtures('clean_db', 'versions_setup')
@pytest.mark.usefixtures('with_plugins')
@pytest.mark.ckan_config('ckan.plugins', 'unaids blob_storage versions')
class TestDatasetReleaseRestore(object):

    def _restore(self, app, user, dataset, release):
        response = app.post(
            url=url_for(
                'unaids_dataset_releases.release_restore',
                dataset_type=dataset['type'],
                dataset_id=dataset['id'],
                release_id=release['id']
            ),
            extra_environ={'REMOTE_USER': user['name']}
        )
        assert response.status_code == 200
        soup = BeautifulSoup(response.body)
        flash_messages = soup.find('div', {'class': 'flash-messages'}).text
        return flash_messages

    def test_restore_with_valid_user(self, app):
        user = factories.User()
        dataset, releases = create_dataset_with_releases(user)
        restored_release = releases[-1].copy()
        flash_message = self._restore(app, user, dataset, restored_release)
        assert_in(
            'Release {} restored'.format(restored_release['name']),
            flash_message
        )
        restored_release['name'] = 'restored_{}'.format(
            restored_release['name'])
        assert_releases_are_exactly(
            user, dataset['id'], releases + [restored_release])

    def test_restore_with_invalid_user(self, app):
        user_1, user_2 = factories.User(), factories.User()
        dataset, releases = create_dataset_with_releases(user_1)
        restored_release = releases[-1].copy()
        flash_message = self._restore(
            app, user_2, dataset, restored_release
        )
        assert_in(SOMETHING_WENT_WRONG_ERROR, flash_message)
        assert_releases_are_exactly(user_1, dataset['id'], releases)


@pytest.mark.usefixtures('clean_db', 'versions_setup')
@pytest.mark.usefixtures('with_plugins')
@pytest.mark.ckan_config('ckan.plugins', 'unaids blob_storage versions')
class TestDatasetReleaseListView(object):

    def test_no_releases_created(self, app):
        user = factories.User()
        dataset, releases = create_dataset_with_releases(user, 0)
        response = get_listview(app, user, dataset)
        assert_in('No releases have been created yet', response.body)
        assert_not_in('ReleasesTableContainer', response.body)

    def test_releases_are_listed_to_owners(self, app):
        user = factories.User()
        dataset, releases = create_dataset_with_releases(user)
        response = get_listview(app, user, dataset)
        for release in releases:
            assert_in(release['name'], response.body)

    def test_releases_are_listed_to_outsiders(self, app):
        user_1, user_2 = factories.User(), factories.User()
        dataset, releases = create_dataset_with_releases(user_1)
        response = get_listview(app, user_2, dataset)
        for release in releases:
            assert_in(release['name'], response.body)

    def test_add_release_button_is_shown_to_owners(self, app):
        user = factories.User()
        dataset, releases = create_dataset_with_releases(user)
        response = get_listview(app, user, dataset)
        assert_in('Add Release', response.body)

    def test_add_release_button_is_not_shown_to_outsiders(self, app):
        user_1, user_2 = factories.User(), factories.User()
        dataset, releases = create_dataset_with_releases(user_1)
        response = get_listview(app, user_2, dataset)
        assert_not_in('Add Release', response.body)
