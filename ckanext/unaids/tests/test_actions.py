"""Tests for plugin.py."""
# encoding: utf-8
from ckan.plugins import toolkit
from ckan.tests.helpers import call_action
from ckan.tests import factories
import pytest
import logging
from pprint import pformat

from ckanext.unaids.tests import get_context

log = logging.getLogger(__name__)


@pytest.mark.ckan_config('ckan.plugins', 'unaids')
@pytest.mark.usefixtures('with_plugins')
class TestGetTableSchema(object):

    def test_schema_returned_successfully(self, ):
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            schema='non_existant_schema'
        )
        log.debug("Resource dict: {}".format(pformat(resource)))
        response = call_action('get_table_schema', {}, resource_id=resource['id'])
        log.debug("Table schema: {}".format(pformat(response)))
        assert response == {}

    def test_empty_dict_returned_for_no_schema(self, ):
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            schema='non_existant_schema'
        )
        log.debug("Resource dict: {}".format(pformat(resource)))
        response = call_action('get_table_schema', {}, resource_id=resource['id'])
        log.debug("Table schema: {}".format(pformat(response)))
        assert response == {}


@pytest.mark.ckan_config('ckan.plugins', 'unaids versions restricted')
@pytest.mark.usefixtures('with_plugins')
class TestDatasetShowForRelease(object):

    @pytest.mark.parametrize("object_ref", [
        "id",
        "name"
    ])
    def test_package_show_displays_release(self, object_ref, test_version, test_dataset, org_editor):
        context = get_context(org_editor)
        new_title = "Updated Title"
        call_action('package_patch',
                    context,
                    id=test_dataset['id'],
                    title=new_title
                    )
        dataset = call_action('package_show',
                              context,
                              id=test_dataset['id'],
                              release_id=test_version[object_ref]
                              )
        assert test_dataset['id'] == dataset['id']
        assert new_title != dataset['title']


    def test_package_show_raises_when_incorrect_release(self, test_dataset, org_editor):
        context = get_context(org_editor)
        with pytest.raises(toolkit.ObjectNotFound, match='Release not found for this dataset'):
            call_action('package_show',
                        context,
                        id=test_dataset['id'],
                        release_id='fake-release-id'
                        )

    @pytest.mark.parametrize("user_role, is_authorized", [
        ('admin', True),
        ('editor', True),
        ('member', True),
    ])
    def test_package_show_auth(self, test_organization, test_dataset, test_version, user_role, is_authorized):
        for user in test_organization['users']:
            context = get_context(user)
            if user['capacity'] == user_role:
                if is_authorized:
                    call_action('package_show',
                                context,
                                id=test_dataset['id'],
                                release_id=test_version['id']
                                )
                    return
                else:
                    with pytest.raises(toolkit.NotAuthorized):
                        call_action('package_show',
                                    context,
                                    id=test_dataset['id'],
                                    release_id=test_version['id']
                                    )
                    return
        pytest.fail("Couldn't find user with required role %s", user_role)


