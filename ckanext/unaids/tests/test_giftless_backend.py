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
        user = factories.User()
        dataset = factories.Dataset(user=user)
        file_name = 'file.csv'
        resource = create_with_upload(
            data='hello,world',
            filename=file_name,
            package_id=dataset['id']
        )
        assert 'sha256' in resource
        assert 'lfs_prefix' in resource
        assert resource.get('name', None) == file_name
