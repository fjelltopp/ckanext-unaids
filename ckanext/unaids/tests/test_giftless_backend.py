# -*- coding: utf-8 -*-

import pytest
from io import BytesIO

from ckan import model
from ckan.plugins import toolkit
from ckan.tests import factories, helpers
from werkzeug.datastructures import FileStorage as FlaskFileStorage
import ckan.lib.helpers as h


@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids authz_service blob_storage scheming_datasets')
@pytest.mark.ckan_config('scheming.presets', 'ckanext.unaids:presets.json ckanext.scheming:presets.json')
@pytest.mark.ckan_config('ckanext.authz_service.jwt_algorithm', 'none')
@pytest.mark.ckan_config('ckanext.authz_service.jwt_private_key', '')
@pytest.mark.ckan_config('ckanext.blob_storage.storage_service_url', 'none')
@pytest.mark.usefixtures('with_plugins', 'clean_db')
class TestGiftlessBackend(object):
    """Test Giftless backend resource creation.
    
    CKAN 2.11 Migration Notes:
    - Added clean_db fixture for test isolation
    - Added scheming_datasets plugin and presets config
    - Added authz_service JWT configuration for none algorithm
    - Issue #24 in ckanext-authz-service was fixed in May 2021
      (PR #25 authz-service + PR #59 blob-storage + PR #131 ckanext-unaids)
    - Python 3: Changed six.StringIO to io.BytesIO for binary data
    """

    @pytest.mark.skip(reason=(
        "Integration test requires running giftless server. "
        "Original issue #24 (context passing) was fixed in ckanext-authz-service PR#25 (May 2021). "
        "Test now fails due to missing giftless infrastructure, not code issues."
    ))
    def test_giftless_resource_create(self):
        user = factories.User()
        org = factories.Organization(
            users=[
                {'name': user['name'], 'capacity': 'admin'},
            ]
        )
        dataset = factories.Dataset(user=user, owner_org=org['id'])
        filename = 'file.csv'
        # Python 3: Use BytesIO for binary data (was six.StringIO)
        csv_stream = BytesIO(b'col1,col2\ntest,file')
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


@pytest.mark.ckan_config('ckan.plugins', 'activity ytp_request unaids pages blob_storage scheming_datasets')
@pytest.mark.usefixtures('with_plugins', 'clean_db')
class TestResourceUrlEncoding():
    """Test resource URL encoding with special characters.
    
    CKAN 2.11 Migration Notes:
    - Added with_plugins and clean_db fixtures for test isolation
    - Added user context to call_action for activity plugin compatibility
    """
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

        # CKAN 2.11: Activity plugin requires user context
        resource = helpers.call_action(
            'resource_create', 
            {'user': user['name']},
            package_id=dataset["id"], 
            url_type='upload',
            url=unquoted_filename,
            lfs_prefix='prefix',
            sha256='acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79',
            size=100,
        )

        resource_read_url = h.url_for(
                "resource.read",
                id=dataset["name"],
                resource_id=resource["id"]
            )
        ressource_read_response = app.get(
            url=resource_read_url
        )

        assert quoted_filename in ressource_read_response.body
