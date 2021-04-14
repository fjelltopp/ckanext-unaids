# -*- coding: utf-8 -*-

import pytest
import ckan.tests.factories as factories
from ckan.tests.helpers import call_action


@pytest.mark.ckan_config('ckan.plugins', 'unaids')
@pytest.mark.usefixtures('with_plugins')
@pytest.mark.usefixtures('clean_db')
@pytest.mark.usefixtures('create_with_upload')
class TestGiftlessBackend(object):

    def test_resource_update(self, create_with_upload):
        dataset = factories.Dataset()
        file_name = 'file.csv'
        resource = create_with_upload(
            data='hello,world',
            filename=file_name,
            package_id=dataset['id']
        )
        assert 'upload' not in resource, \
            'The resource should no longer have a file attached to it'
        assert 'sha256' in resource
        assert 'lfs_prefix' in resource
        assert resource.get('name', None) == file_name
