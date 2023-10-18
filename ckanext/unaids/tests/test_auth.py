'Tests for plugin.py.'
# encoding: utf-8

from ckan.tests import factories, helpers
from contextlib import nullcontext as does_not_raise
import ckan.plugins.toolkit as toolkit
from ckanext.unaids.auth import (
    unaids_organization_update
)
import pytest
import logging
import mock

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
        mock_model = mock.MagicMock()
        mock_model.User.get.return_value = user
        context = {'user': user['name'], 'model': mock_model}
        with outcome:
            helpers.call_auth('dataset_lock', context)
