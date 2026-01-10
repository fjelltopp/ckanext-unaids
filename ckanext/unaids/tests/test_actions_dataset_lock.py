import pytest
from ckan.tests.helpers import call_action
from ckan.tests import factories
from ckanext.unaids.tests import get_context
from ckan.plugins import toolkit


def _create_locked_dataset():
    """Helper function to create a locked dataset. Returns (locked_dataset, user)."""
    user = factories.User(sysadmin=True)
    org = factories.Organization()
    # Create dataset with factory first
    dataset = factories.Dataset(owner_org=org['id'], type='test-schema')
    # Trigger activity creation with package_patch (factories don't create activities)
    call_action('package_patch',
                context={'user': user['name']},
                id=dataset['id'],
                notes='Trigger activity')

    context = get_context(user['name'])
    context['auth_user_obj'] = context['model'].User.get(user['name'])
    call_action('dataset_lock', context, id=dataset['id'])
    locked_dataset = call_action('package_show', id=dataset['id'])
    return locked_dataset, user


@pytest.mark.ckan_config('ckan.plugins', 'ytp_request unaids scheming_datasets activity versions')
@pytest.mark.ckan_config('scheming.dataset_schemas', 'ckanext.unaids.tests.test_scheming_schemas:test_schema.json')
@pytest.mark.ckan_config('scheming.presets', 'ckanext.unaids:presets.json ckanext.scheming:presets.json')
@pytest.mark.usefixtures('with_plugins')
class TestDatasetLock(object):

    @pytest.fixture
    def locked_dataset(self):
        dataset, _ = _create_locked_dataset()
        return dataset

    def test_metadata_updated(self, locked_dataset):
        assert locked_dataset['locked']

    def test_version_created(self, locked_dataset):
        response = call_action('dataset_version_list', dataset_id=locked_dataset['id'])
        assert response[-1]['name'] == 'Locked'

    def test_version_already_created(self):
        user = factories.User(sysadmin=True)
        org = factories.Organization()
        # Create dataset with factory first
        dataset = factories.Dataset(owner_org=org['id'], type='test-schema')
        # Trigger activity creation with package_patch (factories don't create activities)
        call_action('package_patch',
                    context={'user': user['name']},
                    id=dataset['id'],
                    notes='Trigger activity')

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


@pytest.mark.ckan_config('ckan.plugins', 'ytp_request unaids scheming_datasets activity versions')
@pytest.mark.ckan_config('scheming.dataset_schemas', 'ckanext.unaids.tests.test_scheming_schemas:test_schema.json')
@pytest.mark.ckan_config('scheming.presets', 'ckanext.unaids:presets.json ckanext.scheming:presets.json')
@pytest.mark.usefixtures('with_plugins')
class TestDatasetUnlock(object):

    @pytest.fixture
    def locked_dataset_with_user(self):
        return _create_locked_dataset()

    def test_metadata_updated(self, locked_dataset_with_user):
        locked_dataset, user = locked_dataset_with_user
        call_action(
            'dataset_unlock',
            context={'user': user['name']},
            id=locked_dataset['id']
        )
        updated_dataset = call_action(
            'package_show',
            id=locked_dataset['id']
        )
        assert not updated_dataset['locked']

    def test_version_deleted(self, locked_dataset_with_user):
        locked_dataset, user = locked_dataset_with_user
        call_action(
            'dataset_unlock',
            context={'user': user['name']},
            id=locked_dataset['id']
        )
        response = call_action('dataset_version_list', dataset_id=locked_dataset['id'])
        assert not response

    def test_version_already_deleted(self, locked_dataset_with_user):
        locked_dataset, user = locked_dataset_with_user
        versions = call_action('dataset_version_list', dataset_id=locked_dataset['id'])
        call_action(
            "version_delete",
            version_id=versions[-1]["id"],
        )
        with pytest.raises(toolkit.ObjectNotFound):
            call_action(
                'dataset_unlock',
                context={'user': user['name']},
                id=locked_dataset['id']
            )
