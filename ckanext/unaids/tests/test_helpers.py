import pytest
from ckan.tests.helpers import call_action
from ckan.tests import factories
from ckanext.unaids.tests import get_context
from ckan.plugins import toolkit


@pytest.mark.ckan_config('ckan.plugins', 'unaids scheming_datasets versions')
@pytest.mark.usefixtures('with_plugins')
class TestDatasetLock(object):
    def test_dataset_lockable(self):
        dataset = factories.Dataset(type="test-schema")
        assert toolkit.h.dataset_lockable(dataset['id'])

    def test_dataset_not_lockable(self):
        dataset = factories.Dataset()
        assert not toolkit.h.dataset_lockable(dataset['id'])
