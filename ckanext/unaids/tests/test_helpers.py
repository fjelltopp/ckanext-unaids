import pytest
from ckan.tests import factories
from ckan.plugins import toolkit


@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids scheming_datasets versions')
@pytest.mark.ckan_config('scheming.dataset_schemas', 'ckanext.unaids.tests.test_scheming_schemas:test_schema.json')
@pytest.mark.ckan_config('scheming.presets', 'ckanext.unaids:presets.json ckanext.scheming:presets.json')
@pytest.mark.usefixtures('with_plugins', 'clean_db')
class TestDatasetLockHelper(object):
    """Test dataset lock helper functions.

    CKAN 2.11 Migration Notes:
    - Added scheming config markers for test-schema dataset type
    - Added clean_db fixture to ensure clean state
    """

    @pytest.fixture(autouse=True)
    def setup_org(self):
        """Create org and user for dataset creation in CKAN 2.11."""
        self.user = factories.User()
        self.org = factories.Organization(users=[{'name': self.user['id'], 'capacity': 'admin'}])

    def test_dataset_lockable(self):
        dataset = factories.Dataset(
            type="test-schema",
            owner_org=self.org['id'],
            user=self.user
        )
        assert toolkit.h.dataset_lockable(dataset['id'])

    def test_dataset_not_lockable(self):
        dataset = factories.Dataset(owner_org=self.org['id'], user=self.user)
        assert not toolkit.h.dataset_lockable(dataset['id'])

    def test_dataset_not_found(self):
        assert not toolkit.h.dataset_lockable("bad-id")
