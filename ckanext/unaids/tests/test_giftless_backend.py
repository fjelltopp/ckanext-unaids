# -*- coding: utf-8 -*-

import pytest
from six import StringIO

from ckan import model
from ckan.plugins import toolkit
from ckan.tests import factories, helpers
from werkzeug.datastructures import FileStorage as FlaskFileStorage
import ckan.lib.helpers as h


@pytest.mark.ckan_config('ckan.plugins', 'unaids authz_service blob_storage')
@pytest.mark.usefixtures('with_plugins')
class TestGiftlessBackend(object):

    @pytest.mark.skip("doesn't work as long as HTTP auth is used."
                      " Wait for https://github.com/datopian/ckanext-authz-service/issues/24")
    def test_giftless_resource_create(self):
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

        toolkit.get_action('resource_create')(
            context,
            resource
        )
        assert 'sha256' in resource
        assert 'lfs_prefix' in resource
        assert resource.get('name', None) == filename


@pytest.mark.ckan_config('ckan.plugins', 'unaids pages blob_storage')
class TestResourceUrlEncoding():
    def test_resource_url_encoding_test(self, app):
        user = factories.User()
        org = factories.Organization(
            users=[
                {'name': user['name'], 'capacity': 'admin'},
            ]
        )
        dataset = factories.Dataset(user=user, owner_org=org['id'])

        unquoted_filename = 'file%.csv'
        quoted_filename = 'file%25.csv'

        resource = helpers.call_action('resource_create', package_id=dataset["id"], **{
            'url_type': 'upload',
            'url': unquoted_filename,
            'lfs_prefix': 'prefix',
            'sha256': 'acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79',
            'size': 100,
        })

        resource_read_url = h.url_for(
                "resource.read",
                id=dataset["name"],
                resource_id=resource["id"]
            )
        ressource_read_response = app.get(
            url=resource_read_url
        )

        assert quoted_filename in ressource_read_response.body
