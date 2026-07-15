import pytest
from ckan.tests import factories
from ckan.plugins import toolkit
from ckanext.unaids.helpers import (
    get_support_url,
    get_freshdesk_widget_id,
    get_freshdesk_app_name,
)


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


class TestGetFreshdeskWidgetId(object):
    @pytest.mark.parametrize('value,expected', [
        ('157000000691', 157000000691),
        ('  12345  ', 12345),
        ('0', None),
        ('-5', None),
        ('abc', None),
        ('12ab', None),
        ('0};alert(1)//', None),
        ('', None),
        ('9007199254740991', 9007199254740991),
        ('9007199254740992', None),
    ])
    def test_only_positive_int_is_exposed(self, monkeypatch, value, expected):
        monkeypatch.setenv('CKAN_UNAIDS_FRESHDESK_WIDGET_ID', value)
        assert get_freshdesk_widget_id() == expected

    def test_blank_env_falls_back_to_config(self, monkeypatch):
        monkeypatch.setenv('CKAN_UNAIDS_FRESHDESK_WIDGET_ID', '   ')
        monkeypatch.setitem(
            toolkit.config, 'ckanext.unaids.freshdesk_widget_id', '111')
        assert get_freshdesk_widget_id() == 111

    def test_none_when_unset(self, monkeypatch):
        monkeypatch.delenv('CKAN_UNAIDS_FRESHDESK_WIDGET_ID', raising=False)
        monkeypatch.delitem(
            toolkit.config, 'ckanext.unaids.freshdesk_widget_id', raising=False)
        assert get_freshdesk_widget_id() is None

    def test_falls_back_to_config(self, monkeypatch):
        monkeypatch.delenv('CKAN_UNAIDS_FRESHDESK_WIDGET_ID', raising=False)
        monkeypatch.setitem(
            toolkit.config, 'ckanext.unaids.freshdesk_widget_id', '157000000691')
        assert get_freshdesk_widget_id() == 157000000691

    def test_env_takes_precedence_over_config(self, monkeypatch):
        monkeypatch.setitem(
            toolkit.config, 'ckanext.unaids.freshdesk_widget_id', '111')
        monkeypatch.setenv('CKAN_UNAIDS_FRESHDESK_WIDGET_ID', '222')
        assert get_freshdesk_widget_id() == 222


class TestGetFreshdeskAppName(object):
    @pytest.mark.parametrize('value,expected', [
        ('AIDS Data Repository (ADR)', 'AIDS Data Repository (ADR)'),
        ('  AIDS Data Repository (ADR)  ', 'AIDS Data Repository (ADR)'),
        ('', None),
        ('   ', None),
    ])
    def test_env_value(self, monkeypatch, value, expected):
        monkeypatch.setenv('CKAN_UNAIDS_FRESHDESK_APP_NAME', value)
        assert get_freshdesk_app_name() == expected

    def test_none_when_unset(self, monkeypatch):
        monkeypatch.delenv('CKAN_UNAIDS_FRESHDESK_APP_NAME', raising=False)
        monkeypatch.delitem(
            toolkit.config, 'ckanext.unaids.freshdesk_app_name', raising=False)
        assert get_freshdesk_app_name() is None

    def test_blank_env_falls_back_to_config(self, monkeypatch):
        monkeypatch.setenv('CKAN_UNAIDS_FRESHDESK_APP_NAME', '   ')
        monkeypatch.setitem(
            toolkit.config, 'ckanext.unaids.freshdesk_app_name', 'ADR')
        assert get_freshdesk_app_name() == 'ADR'

    def test_env_takes_precedence_over_config(self, monkeypatch):
        monkeypatch.setitem(
            toolkit.config, 'ckanext.unaids.freshdesk_app_name', 'FromConfig')
        monkeypatch.setenv('CKAN_UNAIDS_FRESHDESK_APP_NAME', 'FromEnv')
        assert get_freshdesk_app_name() == 'FromEnv'


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
