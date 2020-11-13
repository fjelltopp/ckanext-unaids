'Tests for plugin.py.'
# encoding: utf-8

from ckan.tests import helpers
import ckan.model as model
from ckan.lib.helpers import url_for
from ckan.tests import factories
from ckan.plugins import toolkit
import pytest
import logging

log = logging.getLogger(__name__)


@pytest.mark.ckan_config('ckan.plugins', 'unaids scheming_datasets')
@pytest.mark.usefixtures('with_plugins')
@pytest.mark.usefixtures('clean_db')
class TestDatasetTransfer(object):

    def test_dataset_transfer_request(self, app):

        # create 3 users and orgs
        user_1, user_2, user_3 = [
            factories.User()
            for x in range(3)
        ]
        org_1, org_2, org_3 = [
            factories.Organization(user=user)
            for user in [user_1, user_2, user_3]
        ]

        # create an org_1 dataset pending transfer to org_2
        dataset = factories.Dataset(
            owner_org=org_1['id'],
            type='test-schema',
            org_to_allow_transfer_to=org_2['id']
        )
        transfer_dataset_url = url_for(
            'unaids_dataset_transfer.process_dataset_transfer',
            dataset_id=dataset['id']
        )

        # user_1 and user_3 should not be able to accept
        # the transfer as they are not members of org_2
        for user in [user_1, user_3]:
            response = app.get(
                url=transfer_dataset_url,
                extra_environ={'REMOTE_USER': user['name']},
                status=403 # expect forbidden error
            )
        
        # user_2 should be able to accept the transfer
        response = app.get(
            url=transfer_dataset_url,
            extra_environ={'REMOTE_USER': user_2['name']},
            status=200
        )

        # confirm dataset was moved to org_2
        result = helpers.call_action(
            'package_show',
            id=dataset['id'],
            context={'user': user_2['name']},
        )
        assert result['owner_org'] == org_2['id']
        assert not result['org_to_allow_transfer_to']