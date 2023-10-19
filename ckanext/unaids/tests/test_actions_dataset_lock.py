import pytest
from ckan.tests.helpers import call_action
from ckan.tests import factories
from ckanext.unaids.tests import get_context
from ckan.plugins import toolkit


@pytest.fixture
def locked_dataset():
    user = factories.User(sysadmin=True)
    dataset = factories.Dataset()
    context = get_context(user['name'])
    context['auth_user_obj'] = context['model'].User.get(user['name'])
    call_action('dataset_lock', context, id=dataset['id'])
    locked_dataset = call_action('package_show', id=dataset['id'])
    return locked_dataset


@pytest.mark.ckan_config('ckan.plugins', 'unaids scheming_datasets versions')
@pytest.mark.usefixtures('with_plugins')
class TestDatasetLock(object):
    def test_metadata_updated(self, locked_dataset):
        assert locked_dataset['locked']

    def test_version_created(self, locked_dataset):
        response = call_action('dataset_version_list', dataset_id=locked_dataset['id'])
        assert response[-1]['name'] == 'Locked'

    def test_version_already_created(self):
        user = factories.User(sysadmin=True)
        dataset = factories.Dataset()
        context = get_context(user['name'])
        context['auth_user_obj'] = context['model'].User.get(user['name'])
        call_action(
            "dataset_version_create",
            context,
            dataset_id=dataset["id"],
            name="Locked"
        )
        with pytest.raises(toolkit.ValidationError):
            call_action('dataset_lock', context, id=dataset['id'])
        dataset = call_action('package_show', id=dataset['id'])
        assert not dataset["locked"], "Dataset shouldn't be locked if release not created"


@pytest.mark.ckan_config('ckan.plugins', 'unaids scheming_datasets versions')
@pytest.mark.usefixtures('with_plugins')
class TestDatasetUnlock(object):
    def test_metadata_updated(self, locked_dataset):
        call_action(
            'dataset_unlock',
            id=locked_dataset['id']
        )
        updated_dataset = call_action(
            'package_show',
            id=locked_dataset['id']
        )
        assert not updated_dataset['locked']

    def test_version_deleted(self, locked_dataset):
        call_action(
            'dataset_unlock',
            id=locked_dataset['id']
        )
        response = call_action('dataset_version_list', dataset_id=locked_dataset['id'])
        assert not response

    def test_version_already_deleted(self, locked_dataset):
        versions = call_action('dataset_version_list', dataset_id=locked_dataset['id'])
        call_action(
            "version_delete",
            version_id=versions[-1]["id"],
        )
        with pytest.raises(toolkit.ObjectNotFound):
            call_action(
                'dataset_unlock',
                id=locked_dataset['id']
            )
