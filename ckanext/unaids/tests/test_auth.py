'Tests for plugin.py.'
# encoding: utf-8

from ckan.tests import factories, helpers
from ckan import model
from contextlib import nullcontext as does_not_raise
import ckan.plugins.toolkit as toolkit
from ckanext.unaids.auth import (
    unaids_organization_update
)
import pytest
import logging

log = logging.getLogger(__name__)


@pytest.mark.ckan_config('ckan.plugins', 'ytp_request unaids scheming_datasets')
@pytest.mark.usefixtures('with_plugins')
class TestAuth(object):

    def test_unaids_organization_update_valid(self, app):
        user = factories.User()
        org = factories.Organization(user=user)
        response = unaids_organization_update(
            {'user': user['name']},
            {'id': org['id']}
        )
        assert response['success']

    def test_unaids_organization_update_invalid(self, app):
        user = factories.User()
        org = factories.Organization()
        response = unaids_organization_update(
            {'user': user['name']},
            {'id': org['id']}
        )
        assert not response['success']

    @pytest.mark.parametrize("sysadmin, outcome", [
        (True, does_not_raise()),
        (False, pytest.raises(toolkit.NotAuthorized))
    ])
    def test_dataset_lock(self, sysadmin, outcome):
        user = factories.User(sysadmin=sysadmin)
        context = {'user': user['name'], 'model': model}
        with outcome:
            helpers.call_auth('dataset_lock', context)

    @pytest.mark.parametrize("sysadmin, editor, locked, outcome", [
        (False, False, False, pytest.raises(toolkit.NotAuthorized)),
        (False, True, False, does_not_raise()),
        (False, False, True, pytest.raises(toolkit.NotAuthorized)),
        (False, True, True, pytest.raises(toolkit.NotAuthorized)),
        (True, False, False, does_not_raise()),
        (True, True, False, does_not_raise()),
        (True, False, True, pytest.raises(toolkit.NotAuthorized)),
        (True, True, True, pytest.raises(toolkit.NotAuthorized))
    ])
    def test_locked_package_update(self, sysadmin, editor, locked, outcome):
        user = factories.User(sysadmin=sysadmin)
        capacity = 'member'
        if editor:
            capacity = 'editor'
        org = factories.Organization(users=[
            {'name': user['id'], 'capacity': capacity}
        ])
        dataset = factories.Dataset(owner_org=org['id'])
        if locked:
            helpers.call_action('dataset_lock', id=dataset['id'])
        dataset = helpers.call_action('package_show', id=dataset['id'])
        with outcome:
            helpers.call_auth(
                'package_update',
                context={'user': user['name'], 'model': model},
                id=dataset['id']
            )
