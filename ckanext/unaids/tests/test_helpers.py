import pytest
from ckan.tests import factories
from ckan.plugins import toolkit
from ckanext.unaids.helpers import get_support_url


class TestGetSupportUrl(object):
    @pytest.mark.parametrize('value,expected', [
        ('https://support.example.org/new', 'https://support.example.org/new'),
        ('  https://support.example.org/new  ', 'https://support.example.org/new'),
        ('HTTPS://support.example.org', 'HTTPS://support.example.org'),
        ('http://support.example.org', None),
        ('javascript:alert(1)', None),
        ('data:text/html,hi', None),
        ('//evil.example.org', None),
        ('/relative/path', None),
        ('https://', None),
        ('https:///no-host', None),
    ])
    def test_only_absolute_https_is_exposed(self, monkeypatch, value, expected):
        monkeypatch.setenv('CKAN_UNAIDS_SUPPORT_URL', value)
        assert get_support_url() == expected

    def test_none_when_unset(self, monkeypatch):
        monkeypatch.delenv('CKAN_UNAIDS_SUPPORT_URL', raising=False)
        monkeypatch.delitem(
            toolkit.config, 'ckanext.unaids.support_url', raising=False)
        assert get_support_url() is None

    def test_falls_back_to_config(self, monkeypatch):
        monkeypatch.delenv('CKAN_UNAIDS_SUPPORT_URL', raising=False)
        monkeypatch.setitem(
            toolkit.config, 'ckanext.unaids.support_url',
            'https://config.example.org/new')
        assert get_support_url() == 'https://config.example.org/new'

    def test_env_takes_precedence_over_config(self, monkeypatch):
        monkeypatch.setitem(
            toolkit.config, 'ckanext.unaids.support_url',
            'https://config.example.org/new')
        monkeypatch.setenv(
            'CKAN_UNAIDS_SUPPORT_URL', 'https://env.example.org/new')
        assert get_support_url() == 'https://env.example.org/new'


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
