# -*- coding: utf-8 -*-

import pytest
from six import StringIO

import ckan.tests.factories as factories
from ckan.plugins import toolkit
from ckan import model
from ckan.tests.helpers import call_action
from werkzeug.datastructures import FileStorage as FlaskFileStorage


@pytest.mark.ckan_config('ckan.plugins', 'unaids authz_service external_storage')
@pytest.mark.usefixtures('with_plugins')
@pytest.mark.usefixtures('clean_db')
@pytest.mark.usefixtures('create_with_upload')
class TestGiftlessBackend(object):

    def test_resource_update(self, create_with_upload):
        user = factories.User()
        org = factories.Organization(
            users=[
                {'name': user['name'], 'capacity': 'admin'},
            ]
        )
        dataset = factories.Dataset(user=user, owner_org=org['id'])
        filename = 'file.csv'
        csv_stream = StringIO(b'col1,col2\ntest,file')
        resource = {
            "name": 'Test',
            "description": "Test resource",
            "url_type": "upload",
            ### old way of passing the file
            "upload": FlaskFileStorage(
                stream=csv_stream,
                content_type="text/csv",
                filename=filename
            ),
            "package_id": dataset["id"]
        }
        context = {
            'model': model,
            'user': user['name']
        }

        result = toolkit.get_action('resource_create')(
            context,
            resource
        )
        assert 'sha256' in resource
        assert 'lfs_prefix' in resource
        assert resource.get('name', None) == filename
