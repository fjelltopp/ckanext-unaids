import pytest
from ckan.tests.helpers import call_action
from ckan.tests import factories


@pytest.fixture
def locked_dataset():
    dataset = factories.Dataset()
    call_action('dataset_lock', id=dataset['id'])
    locked_dataset = call_action('package_show', id=dataset['id'])
    return locked_dataset


@pytest.mark.ckan_config('ckan.plugins', 'unaids scheming_datasets')
@pytest.mark.usefixtures('with_plugins')
class TestDatasetLock(object):
    def test_metadata_updated(self, locked_dataset):
        assert locked_dataset['locked']


@pytest.mark.ckan_config('ckan.plugins', 'unaids scheming_datasets')
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
