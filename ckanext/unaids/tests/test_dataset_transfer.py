# encoding: utf-8
import ckan.model as model
from ckan.tests import helpers
from ckan.lib.helpers import url_for
from ckan.tests import factories
import pytest
import mock

from ckanext.unaids.dataset_transfer.model import init_tables
from ckanext.unaids.dataset_transfer.logic import (
    get_org_admins_with_email_addresses,
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

    def test_get_org_admins_with_email_addresses_two_admins(self, app):
        user_1 = factories.User(email='user_1@example.com')
        user_2 = factories.User(email='user_2@example.com')
        organization = factories.Organization(
            users=[
                {'name': user_1['name'], 'capacity': 'admin'},
                {'name': user_2['name'], 'capacity': 'admin'}
            ]
        )
        returned_users = get_org_admins_with_email_addresses(
            org=organization,
            exclude_user_ids=[user_1['id']]
        )
        returned_user_ids = [x.id for x in returned_users]
        assert returned_user_ids == [user_2['id']]

    def test_get_org_admins_with_email_addresses_one_admin(self, app):
        user_1 = factories.User(email='user_1@example.com')
        user_2 = factories.User(email='user_2@example.com')
        organization = factories.Organization(
            users=[
                {'name': user_1['name'], 'capacity': 'admin'},
                {'name': user_2['name'], 'capacity': 'member'}
            ]
        )
        returned_users = get_org_admins_with_email_addresses(
            org=organization,
            exclude_user_ids=[]
        )
        returned_user_ids = [x.id for x in returned_users]
        assert returned_user_ids == [user_1['id']]

    def test_get_org_admins_with_email_addresses_no_admins(self, app):
        user_1 = factories.User(email='user_1@example.com')
        user_2 = factories.User(email='user_2@example.com')
        organization = factories.Organization(
            users=[
                {'name': user_1['name'], 'capacity': 'member'},
                {'name': user_2['name'], 'capacity': 'member'}
            ]
        )
        returned_users = get_org_admins_with_email_addresses(
            org=organization,
            exclude_user_ids=[]
        )
        assert returned_users == []

    def test_get_org_admins_with_email_addresses_two_orgs(self, app):
        user_1 = factories.User(email='user_1@example.com')
        user_2 = factories.User(email='user_2@example.com')
        organization_1 = factories.Organization(
            users=[{'name': user_1['name'], 'capacity': 'admin'}]
        )
        factories.Organization(
            users=[{'name': user_2['name'], 'capacity': 'admin'}]
        )
        returned_users = get_org_admins_with_email_addresses(
            org=organization_1,
            exclude_user_ids=[]
        )
        returned_user_ids = [x.id for x in returned_users]
        assert returned_user_ids == [user_1['id']]

    def test_get_org_admins_with_no_users_in_org(self, app):
        with pytest.raises(ValueError):
            get_org_admins_with_email_addresses(
                org={'name': 'org_with_no_users'},
                exclude_user_ids=[]
            )

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

    def test_send_dataset_transfer_emails_errors(self, app):
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
        expected_error = r'All DatasetTransferRequest emails failed *'
        with pytest.raises(AssertionError, match=expected_error):
            send_dataset_transfer_emails(
                dataset_id=dataset['id'],
                recipient_org_id=org_2['id']
            )

    def test_dataset_transfer_request(self, app):

        # create 3 users and orgs
        user_1, user_2, user_3 = [
            factories.User(
                email='user_{}_@example.com'.format(x)
            )
            for x in range(3)
        ]
        org_1, org_2, org_3 = [
            factories.Organization(
                owner=user,
                users=[{'name': user['name'], 'capacity': 'admin'}]
            )
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
        assert 'org_to_allow_transfer_to' not in result
