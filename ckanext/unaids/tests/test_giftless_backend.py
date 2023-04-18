# -*- coding: utf-8 -*-

import pytest
from six import StringIO

from ckan import model
from ckan.plugins import toolkit
from ckan.tests import factories
from werkzeug.datastructures import FileStorage as FlaskFileStorage
from ckan.tests import factories, helpers
import ckan.lib.helpers as h
from urllib.parse import unquote
from .. import helpers as unaids_helpers



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


    def test_resource_url_encoding_test(self):
        user = factories.User()
        org = factories.Organization(
            users=[
                {'name': user['name'], 'capacity': 'admin'},
            ]
        )
        dataset = factories.Dataset(user=user, owner_org=org['id'])
        filename = 'file%.csv'
        resource = helpers.call_action('resource_create', package_id=dataset["id"], name=filename)
        url = h.url_for('resource.view',
                                    id=dataset['id'],
                                    resource_id=resource['id'],
                                    filename=filename,
                                    qualified=True)

        url_not_encoded = unquote(url)
        assert unaids_helpers.url_encode(url_not_encoded) == url