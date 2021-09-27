'Tests for plugin.py.'
# encoding: utf-8

from ckan.tests import factories
import pytest
import ckan.lib.navl.dictization_functions as df
from ckanext.unaids.validators import organization_id_exists_validator, if_empty_guess_format


@pytest.mark.ckan_config('ckan.plugins', 'unaids scheming_datasets')
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
        (None,  None, 'http://adr.local/dataset/0f0cae9cea61/resource/891922a0f614/download/demo.csv', 'text/csv'),
        (None,  None, 'http://adr.local/dataset/0f0cae9cea61/resource/891922a0f614/download/demo.geojson', 'application/geo+json'),
        (None,  None, 'http://adr.local/dataset/0f0cae9cea61/resource/891922a0f614/download/demo.pjnz', 'application/pjnz'),
        ('text/csv',  '891922a0f614', 'http://adr.local/dataset/0f0cae9cea61/resource/891922a0f614/download/demo.xlsx', 'text/csv'),
        (None,  '891922a0f614', 'http://adr.local/dataset/0f0cae9cea61/resource/891922a0f614/download/demo.csv', None),

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
