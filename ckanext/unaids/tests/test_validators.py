'Tests for plugin.py.'
# encoding: utf-8

from ckan.tests import factories
import pytest
import ckan.lib.navl.dictization_functions as df
from ckanext.unaids.validators import organization_id_exists_validator


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
