import pytest
from ckan.tests import factories
from ckan.plugins import toolkit
from ckanext.unaids.helpers import get_support_url


class TestGetSupportUrl(object):
    @pytest.mark.parametrize('value,expected', [
        ('https://support.example.org/new', 'https://support.example.org/new'),
        ('  https://support.example.org/new  ', 'https://support.example.org/new'),
        ('http://support.example.org', None),
        ('javascript:alert(1)', None),
        ('data:text/html,hi', None),
        ('/relative/path', None),
    ])
    def test_only_absolute_https_is_exposed(self, monkeypatch, value, expected):
        monkeypatch.setenv('CKAN_UNAIDS_SUPPORT_URL', value)
        assert get_support_url() == expected


@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids scheming_datasets versions')
@pytest.mark.usefixtures('with_plugins')
class TestDatasetLockHelper(object):
    def test_dataset_lockable(self):
        dataset = factories.Dataset(type="test-schema")
        assert toolkit.h.dataset_lockable(dataset['id'])

    def test_dataset_not_lockable(self):
        dataset = factories.Dataset()
        assert not toolkit.h.dataset_lockable(dataset['id'])

    def test_dataset_not_found(self):
        assert not toolkit.h.dataset_lockable("bad-id")
