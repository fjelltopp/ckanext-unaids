'Tests for plugin.py.'
# encoding: utf-8
from ckanext.unaids.validators import organization_id_exists_validator
from ckanext.unaids.auth import unaids_organization_update
from ckan.tests import helpers
from ckan.lib.helpers import url_for
from ckan.tests import factories
import pytest
import logging

log = logging.getLogger(__name__)


@pytest.mark.ckan_config('ckan.plugins', 'unaids scheming_datasets')
@pytest.mark.usefixtures('with_plugins')
@pytest.mark.usefixtures('clean_db')
class TestDatasetTransfer(object):

    def test_organisation_update_authorization(self):
        user = factories.User()
        org = factories.Organization(users=[{'name': user['id'], 'capacity': 'admin'}])
        unaids_organization_update({'user': user['id']}, {'id': org['id']})

    def test_organisation_id_exists_validator(self):
        org = factories.Organization()
        organization_id_exists_validator(
            'organization_to_allow_transfer_to',
            {'organization_to_allow_transfer_to': org['id']},
            {},
            {}
        )

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
            )
            assert response.status_code == 403

        # user_2 should be able to accept the transfer
        app.get(
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
