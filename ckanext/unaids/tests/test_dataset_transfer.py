'Tests for plugin.py.'
# encoding: utf-8
import ckan.model as model
from ckan.tests import helpers
from ckan.lib.helpers import url_for
from ckan.tests import factories
import pytest
import mock

from ckanext.unaids.dataset_transfer.model import (
    DatasetTransferRequest,
    init_tables
)
from ckanext.unaids.dataset_transfer.logic import (
    _get_users_to_email,
    send_dataset_transfer_emails
)

@pytest.fixture
def initdb():
    model.Session.remove()
    model.Session.configure(bind=model.meta.engine)
    init_tables()

@pytest.mark.usefixtures('initdb')
@pytest.mark.ckan_config('ckan.plugins', 'unaids scheming_datasets')
@pytest.mark.usefixtures('with_plugins')
@pytest.mark.usefixtures('clean_db')
class TestDatasetTransfer(object):

    @mock.patch('ckan.lib.mailer.mail_user')
    def test_send_dataset_transfer_emails(self, mocked_mail_user, app):
        user_1, user_2 = [
            factories.User()
            for x in range(2)
        ]
        org_1, org_2 = [
            factories.Organization(user=user)
            for user in [user_1, user_2]
        ]
        dataset = factories.Dataset(
            owner_org=org_1['id'],
            type='test-schema',
            org_to_allow_transfer_to=org_2['id']
        )
        send_dataset_transfer_emails(
            dataset_id=dataset['id'],
            recipient_org_id=org_2['id']
        )
        mocked_mail_user.assert_called()
        emailed_user_ids = [
            x[0][0].id  # recipient_user_id
            for x in mocked_mail_user.call_args_list
        ]
        assert emailed_user_ids == [user_2['id']]

    def test_get_users_to_email(self, app):
        owner, admin_1, admin_2, editor, member = [
            factories.User(name=name)
            for name in ['owner', 'admin_1', 'admin_2', 'editor', 'member']
        ]
        organization = factories.Organization(
            user=owner,
            users=[
                {'name': admin_1['id'], 'capacity': 'admin'},
                {'name': admin_2['id'], 'capacity': 'admin'},
                {'name': editor['id'], 'capacity': 'editor'},
                {'name': member['id'], 'capacity': 'member'}
            ]
        )
        all_users_to_email = _get_users_to_email(
            recipient_org=organization,
            exclude_user_ids=[admin_2['id']]
        )
        user_ids_to_email = [x.id for x in all_users_to_email]
        for user in [owner, admin_1]:
            assert user['id'] in user_ids_to_email, \
                'Dataset org {} should be emailed'.format(user['name'])
        for user in [editor, member, admin_2]:
            assert user['id'] not in user_ids_to_email, \
                'Dataset org {} should NOT be emailed'.format(user['name'])
                
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
