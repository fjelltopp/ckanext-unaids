'Tests for plugin.py.'
# encoding: utf-8

from ckan.tests import factories
import pytest
import ckan.lib.navl.dictization_functions as df
from contextlib import nullcontext as does_not_raise
import ckan.plugins.toolkit as toolkit
from ckanext.unaids.validators import (
    organization_id_exists_validator,
    if_empty_guess_format,
    read_only
)


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
        ({'package': {'locked': True}}, does_not_raise()),
        ({'package': {'locked': False}}, pytest.raises(toolkit.Invalid)),
        ({'package': {'locked': True}, 'bypass_read_only': True}, does_not_raise()),
        ({'package': {'locked': False}, 'bypass_read_only': True}, does_not_raise()),
        ({'package': {'locked': True}, 'bypass_read_only': False}, does_not_raise()),
        ({'package': {'locked': False}, 'bypass_read_only': False}, pytest.raises(toolkit.Invalid))
    ])
    def test_read_only(self, context, result):
        with result:
            read_only('locked', {'locked': True}, [], context)
