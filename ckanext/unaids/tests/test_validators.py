'Tests for plugin.py.'
# encoding: utf-8

from ckan.tests import factories
import pytest
import ckan.lib.navl.dictization_functions as df
from contextlib import nullcontext as does_not_raise
import ckan.plugins.toolkit as toolkit
from ckan.tests.helpers import call_action
from ckanext.unaids.validators import (
    organization_id_exists_validator,
    if_empty_guess_format,
    read_only
)
from mock import MagicMock


@pytest.fixture
def read_only_validator():
    test_schema = call_action('scheming_dataset_schema_show', type="test-schema")
    read_only_field = None
    for field in test_schema['dataset_fields']:
        if field['field_name'] == 'locked':
            read_only_field = field
    return read_only(read_only_field, test_schema)


@pytest.mark.ckan_config('ckan.plugins', 'ytp_request unaids scheming_datasets')
@pytest.mark.usefixtures('with_plugins')
class TestValidators(object):

    def test_organisation_id_exists_validator(self):
        valid_org_id = factories.Organization()['id']
        organization_id_exists_validator(
            'organization_id',
            {'organization_id': valid_org_id},
            {},
            {}
        )
        invalid_org_id = 'this is an invalid org id'
        with pytest.raises(df.Invalid):
            organization_id_exists_validator(
                'organization_id',
                {'organization_id': invalid_org_id},
                {},
                {}
            )

    @pytest.mark.parametrize("format,resource_id,url,result", [
        (None,  None, 'http://adr.local/resource/8919/demo.csv', 'text/csv'),
        (None,  None, 'http://adr.local/resource/8919/demo.geojson', 'application/geo+json'),
        (None,  None, 'http://adr.local/resource/8919/demo.pjnz', 'application/pjnz'),
        ('text/csv',  '8919', 'http://adr.local/resource/89192/demo.xlsx', 'text/csv'),
        (None,  '8919', 'http://adr.local/resource/8919/demo.csv', None)
    ])
    def test_if_empty_guess_format(self, url, resource_id, format, result):
        key = (u'resources', 0, 'format')
        data = {
            (u'resources', 0, 'format'): format,
            (u'resources', 0, 'id'): resource_id,
            (u'resources', 0, 'url'): url
        }
        if_empty_guess_format(key, data, {}, {})
        assert data[key] == result

    @pytest.mark.parametrize("context, result", [
        ({},  pytest.raises(toolkit.Invalid)),
        ({'bypass_read_only': True},  does_not_raise()),
        ({'bypass_read_only': False},  pytest.raises(toolkit.Invalid)),
        ({'package': MagicMock(extras={'locked': True})}, does_not_raise()),
        ({'package': MagicMock(extras={'locked': False})}, pytest.raises(toolkit.Invalid)),
        ({'package': MagicMock(extras={'locked': True}), 'bypass_read_only': True}, does_not_raise()),
        ({'package': MagicMock(extras={'locked': False}), 'bypass_read_only': True}, does_not_raise()),
        ({'package': MagicMock(extras={'locked': True}), 'bypass_read_only': False}, does_not_raise()),
        ({'package': MagicMock(extras={'locked': False}), 'bypass_read_only': False}, pytest.raises(toolkit.Invalid))
    ])
    def test_read_only_raises(self, context, result, read_only_validator):
        with result:
            read_only_validator('locked', {'locked': True}, [], context)

    @pytest.mark.parametrize("context, data, result", [
        ({}, {}, 'false'),
        ({'package': MagicMock(extras={})}, {}, 'false')
    ])
    def test_read_only_sets_default_value(self, context, data, result, read_only_validator):
        read_only_validator(('locked',), data, [], context)
        assert data.get(('locked',)) == result
