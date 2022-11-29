'Tests for plugin.py.'
# encoding: utf-8

from ckan.tests import factories
from ckanext.unaids.auth import (
    unaids_organization_update
)
from ckanext.unaids.tests.factories import User
import pytest
import logging

log = logging.getLogger(__name__)


@pytest.mark.ckan_config('ckan.plugins', 'unaids scheming_datasets')
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
