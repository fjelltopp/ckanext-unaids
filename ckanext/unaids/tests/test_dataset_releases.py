# -*- coding: utf-8 -*-

import pytest
from bs4 import BeautifulSoup
from ckan.lib.helpers import url_for
from ckanext.unaids.tests import create_dataset_with_releases
from ckan.plugins import toolkit
from ckan.tests import factories as ckan_factories
from ckan.tests.factories import User
from ckanext.versions.logic.dataset_version_action import (
    dataset_version_create,
    dataset_version_list,
)
from ckanext.versions.tests import get_context
from ckanext.unaids.blueprints.unaids_dataset_releases import (
    AUTHORIZATION_ERROR,
    RELEASE_ALREADY_EXISTS_FOR_ACTIVITY_ERROR,
    RELEASE_NAME_NOT_UNIQUE_ERROR,
)


def assert_equals(a, b):
    assert a == b


def assert_in(a, b):
    assert a in b


def assert_not_in(a, b):
    assert a not in b


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


@pytest.mark.usefixtures('with_plugins')
@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids blob_storage versions pages scheming_datasets')
class TestDatasetReleaseCreateAndEdit(object):

    def _create_or_edit(self, app, user, dataset, release, activity_id=None):
        response = app.post(
            url=url_for(
                'unaids_dataset_releases.release_view',
                dataset_type=dataset['type'],
                dataset_id=dataset['id'],
                release_id=release.get('id'),
                activity_id=activity_id
            ),
            data=release,
            extra_environ={'REMOTE_USER': user['name']}
        )
        assert response.status_code == 200
        return response.body

    def _get_flash_message(self, response):
        soup = BeautifulSoup(response)
        return soup.find('div', {'class': 'flash-messages'}).text

    def _get_form_errors(self, response):
        soup = BeautifulSoup(response)
        return soup.find('span', {'class': 'error-block'}).text

    def test_create_with_valid_user(self, app):
        user = User()
        dataset, releases = create_dataset_with_releases(user)
        release = {'name': 'my-new-release', 'notes': 'example'}
        response = self._create_or_edit(app, user, dataset, release)
        flash_message = self._get_flash_message(response)
        assert_in('Release {} added'.format(release['name']), flash_message)
        assert_releases_are_exactly(user, dataset['id'], releases + [release])

    def test_create_with_invalid_user(self, app):
        user_1, user_2 = User(), User()
        dataset, releases = create_dataset_with_releases(user_1)
        release = {'name': 'my-new-release', 'notes': 'example'}
        response = self._create_or_edit(
            app, user_2, dataset, release
        )
        flash_message = self._get_flash_message(response)
        assert_in(AUTHORIZATION_ERROR, flash_message)
        assert_releases_are_exactly(user_1, dataset['id'], releases)

    def test_create_with_existing_activity_id(self, app):
        user = User()
        dataset, releases = create_dataset_with_releases(user)
        release = {'name': 'my-new-release', 'notes': 'example'}
        response = self._create_or_edit(
            app, user, dataset, release,
            activity_id=releases[0]['activity_id']
        )
        flash_message = self._get_flash_message(response)
        assert_in(RELEASE_ALREADY_EXISTS_FOR_ACTIVITY_ERROR, flash_message)
        assert_releases_are_exactly(user, dataset['id'], releases)

    def test_create_with_existing_release_name(self, app):
        user = User()
        dataset, releases = create_dataset_with_releases(user)
        release = {'name': releases[0]['name'], 'notes': 'example'}
        response = self._create_or_edit(
            app, user, dataset, release
        )
        form_errors = self._get_form_errors(response)
        assert_in(RELEASE_NAME_NOT_UNIQUE_ERROR, form_errors)
        assert_releases_are_exactly(user, dataset['id'], releases)

    def test_edit_with_valid_user(self, app):
        user = User()
        dataset, releases = create_dataset_with_releases(user)
        updated_release = releases[0]
        updated_release['name'] = 'updated-release-name'
        response = self._create_or_edit(
            app, user, dataset, updated_release
        )
        flash_message = self._get_flash_message(response)
        assert_in('Release {} updated'.format(
            updated_release['name']), flash_message)
        assert_releases_are_exactly(user, dataset['id'], releases)

    def test_edit_with_invalid_user(self, app):
        user_1, user_2 = User(), User()
        dataset, releases = create_dataset_with_releases(user_1)
        updated_release = releases[0].copy()
        updated_release['name'] = 'updated-release-name'
        response = self._create_or_edit(
            app, user_2, dataset, updated_release
        )
        flash_message = self._get_flash_message(response)
        assert_in(AUTHORIZATION_ERROR, flash_message)
        assert_releases_are_exactly(user_1, dataset['id'], releases)


@pytest.mark.usefixtures('with_plugins')
@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids blob_storage versions pages scheming_datasets')
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
        user = User()
        dataset, releases = create_dataset_with_releases(user)
        deleted_release = releases.pop()
        flash_message = self._delete(app, user, dataset, deleted_release)
        assert_in(
            'Release {} deleted'.format(deleted_release['name']),
            flash_message
        )
        assert_releases_are_exactly(user, dataset['id'], releases)

    def test_delete_with_invalid_user(self, app):
        user_1, user_2 = User(), User()
        dataset, releases = create_dataset_with_releases(user_1)
        deleted_release = releases[0]
        flash_message = self._delete(
            app, user_2, dataset, deleted_release
        )
        assert_in(AUTHORIZATION_ERROR, flash_message)
        assert_releases_are_exactly(user_1, dataset['id'], releases)


@pytest.mark.usefixtures('with_plugins')
@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids blob_storage versions pages scheming_datasets')
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
        user = User()
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
        user_1, user_2 = User(), User()
        dataset, releases = create_dataset_with_releases(user_1)
        restored_release = releases[-1].copy()
        flash_message = self._restore(
            app, user_2, dataset, restored_release
        )
        assert_in(AUTHORIZATION_ERROR, flash_message)
        assert_releases_are_exactly(user_1, dataset['id'], releases)


@pytest.mark.usefixtures('with_plugins')
@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids blob_storage versions pages scheming_datasets')
class TestDatasetReleaseListView(object):

    def test_no_releases_created(self, app):
        user = User()
        dataset, releases = create_dataset_with_releases(user, 0)
        response = get_listview(app, user, dataset)
        assert_in('No releases have been created yet', response.body)
        assert_not_in('ReleasesTableContainer', response.body)

    def test_releases_are_listed_to_owners(self, app):
        user = User()
        dataset, releases = create_dataset_with_releases(user)
        response = get_listview(app, user, dataset)
        for release in releases:
            assert_in(release['name'], response.body)

    def test_releases_are_listed_to_outsiders(self, app):
        user_1, user_2 = User(), User()
        dataset, releases = create_dataset_with_releases(user_1)
        response = get_listview(app, user_2, dataset)
        for release in releases:
            assert_in(release['name'], response.body)

    def test_add_release_button_is_shown_to_owners(self, app):
        user = User()
        dataset, releases = create_dataset_with_releases(user)
        response = get_listview(app, user, dataset)
        assert_in('Add Release', response.body)

    def test_add_release_button_is_not_shown_to_outsiders(self, app):
        user_1, user_2 = User(), User()
        dataset, releases = create_dataset_with_releases(user_1)
        response = get_listview(app, user_2, dataset)
        assert_not_in('Add Release', response.body)


@pytest.mark.usefixtures('with_plugins')
@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids blob_storage versions pages scheming_datasets')
class TestDatasetRead(object):

    def _get_dataset_release_sidebar(self, app, user, dataset, activity_id=None):
        response = app.get(
            url=url_for(
                'dataset.read',
                id=dataset['name'],
                activity_id=activity_id
            ),
            extra_environ={'REMOTE_USER': user['name']}
        )
        assert response.status_code == 200
        soup = BeautifulSoup(response.body)
        return soup.find(id='ReleasesSidebar').text

    def test_activity_id_query_param(self, app):
        user = User()
        dataset, releases = create_dataset_with_releases(user)
        release = releases[0]
        response = self._get_dataset_release_sidebar(
            app, user, dataset, activity_id=release['activity_id']
        )
        assert_in(release['name'], response)
        assert_in(release['notes'], response)
        assert_not_in('Create Release', response)

    def test_when_no_release_for_dataset(self, app):
        user = User()
        dataset, releases = create_dataset_with_releases(user)
        response = self._get_dataset_release_sidebar(app, user, dataset)
        assert_in('no release associated', response)
        assert_in('Add Release', response)

    def test_when_on_latest_version_of_dataset_has_release(self, app):
        user = User()
        dataset, releases = create_dataset_with_releases(user)
        release = dataset_version_create(
            get_context(user),
            {
                'dataset_id': dataset['id'],
                'name': 'my-new-release',
                'notes': 'example',
            }
        )
        response = self._get_dataset_release_sidebar(app, user, dataset)
        assert_in(release['name'], response)
        assert_in(release['notes'], response)
        assert_not_in('Create Release', response)


@pytest.mark.usefixtures('with_plugins')
@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids blob_storage versions pages scheming_datasets')
class TestOldVersionPages(object):
    """Pages showing an old version (release) of a dataset and its resources."""

    @pytest.fixture
    def release(self):
        user = User()
        org = ckan_factories.Organization(user=user)
        dataset = ckan_factories.Dataset(user=user, owner_org=org['id'])
        resource = ckan_factories.Resource(
            package_id=dataset['id'], name='data.csv', url='data.csv', url_type='upload',
            sha256='a' * 64, size=10, lfs_prefix='test-org/test-dataset',
        )
        # A package change after adding the resource, so that the newest
        # activity is one whose stored dataset contains the resource.
        toolkit.get_action('package_patch')(get_context(user), {'id': dataset['id'], 'title': 'released-title'})
        activities = toolkit.get_action('package_activity_list')(get_context(user), {'id': dataset['id']})
        release = dataset_version_create(
            get_context(user),
            {'dataset_id': dataset['id'], 'activity_id': activities[0]['id'], 'name': 'v1'}
        )
        # Make the current version differ from the release
        toolkit.get_action('package_patch')(get_context(user), {'id': dataset['id'], 'title': 'newer-title'})
        return {'user': user, 'dataset': dataset, 'resource': resource, 'release': release}

    def _get(self, app, endpoint, release, **kwargs):
        response = app.get(
            url=url_for(endpoint, id=release['dataset']['id'],
                        activity_id=release['release']['activity_id'], **kwargs),
            extra_environ={'REMOTE_USER': release['user']['name']},
        )
        return BeautifulSoup(response.body, 'html.parser')

    @staticmethod
    def _old_version_notices(soup):
        return [a for a in soup.select('.alert-danger') if 'old version' in a.text]

    @staticmethod
    def _download_hrefs(soup):
        return [a['href'] for a in soup.find_all('a', href=True) if 'download' in a['href']]

    def test_dataset_page_shows_a_single_old_version_notice(self, app, release):
        soup = self._get(app, 'activity.package_history', release)

        notices = self._old_version_notices(soup)
        assert len(notices) == 1
        # The data files of every release are stored, so there must be no warning
        assert 'may not match' not in notices[0].text

    def test_resource_page_shows_a_single_old_version_notice(self, app, release):
        soup = self._get(app, 'activity.resource_history', release, resource_id=release['resource']['id'])

        notices = self._old_version_notices(soup)
        assert len(notices) == 1
        assert 'may not match' not in notices[0].text

    def test_dataset_page_download_links_use_the_release_activity_id(self, app, release):
        soup = self._get(app, 'activity.package_history', release)

        hrefs = self._download_hrefs(soup)
        assert hrefs
        for href in hrefs:
            assert 'activity_id={}'.format(release['release']['activity_id']) in href

    def test_resource_page_download_links_use_the_release_activity_id(self, app, release):
        soup = self._get(app, 'activity.resource_history', release, resource_id=release['resource']['id'])

        hrefs = self._download_hrefs(soup)
        assert hrefs
        for href in hrefs:
            assert 'activity_id={}'.format(release['release']['activity_id']) in href
