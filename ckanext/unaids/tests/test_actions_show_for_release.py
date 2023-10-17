import pytest
from ckanext.unaids.tests import get_context
from ckan.tests.helpers import call_action
from ckan.plugins import toolkit


@pytest.mark.ckan_config(
    'ckan.plugins',
    'unaids versions restricted blob_storage scheming_datasets'
)
@pytest.mark.usefixtures('with_plugins')
class TestDatasetShowForRelease(object):

    @pytest.mark.parametrize("object_ref", [
        "id",
        "name"
    ])
    def test_package_show_displays_release(self, object_ref,
                                           test_version, test_dataset, org_editor):
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
                              release=test_version[object_ref]
                              )
        assert test_dataset['id'] == dataset['id']
        assert new_title != dataset['title']

    def test_package_show_raises_when_incorrect_release(self, test_dataset, org_editor):
        context = get_context(org_editor)
        with pytest.raises(toolkit.ObjectNotFound, match='Release not found'):
            call_action('package_show',
                        context,
                        id=test_dataset['id'],
                        release='fake-release-id'
                        )

    def test_package_show_returns_correct_download_links(self, test_dataset, org_editor):
        context = get_context(org_editor)
        toolkit.get_action('resource_create')(context, {
            "name": 'Test',
            "description": "Test resource",
            "url_type": "upload",
            "lfs_prefix": "test/prefix",
            "filename": "test.csv",
            "sha256": "acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79",
            "size": 50,
            "package_id": test_dataset["id"]
        })
        version = toolkit.get_action('dataset_version_create')(
            context,
            {
                "dataset_id": test_dataset['id'],
                "name": "V1.0"
            }
        )

        dataset = call_action('package_show',
                              context,
                              id=test_dataset['id'],
                              release=version['name']
                              )
        download_link = dataset['resources'][0]['url']
        assert 'activity_id={}'.format(version['activity_id']) in download_link

    def test_package_show_only_returns_updated_resource_download_links_for_uploads(
            self, test_dataset, org_editor, test_resource):
        context = get_context(org_editor)
        version = toolkit.get_action('dataset_version_create')(context, {
                "dataset_id": test_dataset['id'],
                "name": "V1.0"
        })
        dataset = call_action(
            'package_show',
            context,
            id=test_dataset['id'],
            release=version['name']
        )
        download_link = dataset['resources'][0]['url']
        assert 'activity_id={}'.format(version['activity_id']) not in download_link

    @pytest.mark.parametrize("user_role, is_authorized", [
        ('admin', True),
        ('editor', True),
        ('member', True),
    ])
    def test_package_show_auth(self, test_organization, test_dataset,
                               test_version, user_role, is_authorized):
        for user in test_organization['users']:
            context = get_context(user)
            if user['capacity'] == user_role:
                if is_authorized:
                    call_action('package_show',
                                context,
                                id=test_dataset['id'],
                                release=test_version['id']
                                )
                    return
                else:
                    with pytest.raises(toolkit.NotAuthorized):
                        call_action('package_show',
                                    context,
                                    id=test_dataset['id'],
                                    release=test_version['id']
                                    )
                    return
        pytest.fail("Couldn't find user with required role %s", user_role)
