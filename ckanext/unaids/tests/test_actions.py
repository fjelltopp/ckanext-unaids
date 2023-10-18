"""Tests for plugin.py."""
# encoding: utf-8
from ckan.plugins import toolkit
from ckan.tests.helpers import call_action
from ckan.tests import factories
from ckan.logic import NotAuthorized  # , ValidationError
import ckan.model as model
import pytest
import logging
from pprint import pformat
from ckanext.unaids.custom_user_profile.logic import read_saml_profile
from ckanext.unaids.tests import get_context, create_dataset_with_releases

log = logging.getLogger(__name__)


@pytest.mark.ckan_config('ckan.plugins', 'unaids blob_storage scheming_datasets')
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


@pytest.mark.ckan_config('ckan.plugins', 'unaids versions restricted blob_storage scheming_datasets')
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
                              release=test_version[object_ref]
                              )
        assert test_dataset['id'] == dataset['id']
        assert new_title != dataset['title']

    def test_package_show_raises_when_incorrect_release(self, test_dataset, org_editor):
        context = get_context(org_editor)
        with pytest.raises(toolkit.ObjectNotFound, match='Release not found for this dataset'):
            call_action('package_show',
                        context,
                        id=test_dataset['id'],
                        release='fake-release-id'
                        )

    def test_package_show_returns_updated_resource_download_links(self, test_dataset, org_editor):
        context = get_context(org_editor)
        toolkit.get_action('resource_create')(
            context,
            {
                "name": 'Test',
                "description": "Test resource",
                "url_type": "upload",
                "lfs_prefix": "test/prefix",
                "filename": "test.csv",
                "sha256": "acbac3b78f9ace071ca3a79f23fc788a1b7ee9dc547becc6404dbb1f58afff79",
                "size": 50,
                "package_id": test_dataset["id"]
            }
        )
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
        assert 'activity_id={}'.format(version['activity_id']) in dataset['resources'][0]['url']

    def test_package_show_only_returns_updated_resource_download_links_for_uploads(
            self, test_dataset, org_editor, test_resource):
        context = get_context(org_editor)
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
        assert 'activity_id={}'.format(version['activity_id']) not in dataset['resources'][0]['url']

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


@pytest.mark.ckan_config('ckan.plugins', 'unaids versions scheming_datasets')
@pytest.mark.usefixtures('with_plugins')
class TestPackageActivityList(object):

    def test_package_activity_list_containes_releases_names(self, org_editor):
        context = get_context(org_editor)
        dataset, releases = create_dataset_with_releases(org_editor)
        activity_list = call_action('package_activity_list', context, id=dataset['id'])
        for release, activity in zip(releases, reversed(activity_list)):
            assert release['name'] == activity.get('release_name')
        pass


@pytest.mark.ckan_config('ckan.plugins', 'unaids')
@pytest.mark.usefixtures('with_plugins')
class TestFormatGuess(object):

    @pytest.mark.parametrize("filename,mimetype,format", [
        ('art.csv', 'text/csv', 'CSV'),
        ('anc.xls', 'application/vnd.ms-excel', 'XLS'),
        ('country_regions.geojson', 'application/geo+json', 'GeoJSON'),
        ('spectrum_file.pjnz', 'application/pjnz', 'PJNZ'),
        ('no_file_extension', None, None),
        ('', None, None),
    ])
    def test_format_guess_csv(self, filename, mimetype, format):
        response = call_action('format_guess', {}, filename=filename)
        assert response.get('mimetype') == mimetype
        assert response.get('format') == format


@pytest.mark.ckan_config('ckan.plugins', 'unaids')
@pytest.mark.usefixtures('with_plugins')
class TestUserShowMe(object):

    def test_no_user(self):
        with pytest.raises(NotAuthorized):
            call_action('user_show_me', {})

    def test_user(self):
        user = factories.User()
        user_obj = model.User.get(user['name'])
        response = call_action('user_show_me', {'auth_user_obj': user_obj})
        assert response['name'] == user['name']


@pytest.mark.ckan_config('ckan.plugins', 'unaids scheming_datasets')
@pytest.mark.usefixtures('with_plugins')
class TestPopulateDataDictionary(object):

    def test_expected_use(self, mocker):
        dataset = factories.Dataset()
        resource = factories.Resource(
            package_id=dataset['id'],
            schema='test_schema',
        )

        mock_populate_data_dictionary_from_schema = mocker.patch(
            'ckanext.unaids.actions.populate_data_dictionary_from_schema',
        )
        call_action('populate_data_dictionary', {}, resource_id=resource['id'])
        mock_populate_data_dictionary_from_schema.assert_called_once_with(mocker.ANY, resource)


@pytest.mark.ckan_config('ckan.plugins', 'unaids')
@pytest.mark.usefixtures('with_plugins')
class TestUserAffiliation(object):
    def test_user_show_with_affiliation(self):
        user = factories.User()
        user_obj = model.User.get(user["id"])

        read_saml_profile(
            user_obj,
            {
                "job_title": ["Data Scientist"],
                "affiliation": ["Fjelltopp"],
            },
        )
        response = call_action("user_show", id=user["id"])
        assert response.get("job_title", False) == "Data Scientist"
        assert response.get("affiliation", False) == "Fjelltopp"

    def test_user_list_all_fields_with_affiliation(self):
        for i in range(4):
            user = factories.User(name=f"test-user-{i}")
            user_obj = model.User.get(user["id"])

            read_saml_profile(
                user_obj,
                {
                    "job_title": ["Data Scientist"],
                    "affiliation": ["Fjelltopp"],
                },
            )
        response = call_action("user_list")
        for user in response:
            assert user.get("job_title", False) == "Data Scientist"
            assert user.get("affiliation", False) == "Fjelltopp"

    def test_user_list_usernames(self):
        for i in range(4):
            user = factories.User(name=f"test-user-{i}")
            user_obj = model.User.get(user["id"])

            read_saml_profile(
                user_obj,
                {
                    "job_title": ["Data Scientist"],
                    "affiliation": ["Fjelltopp"],
                },
            )
        response = call_action("user_list", all_fields=False)
        assert set(response) == {'test-user-0', 'test-user-1', 'test-user-2', 'test-user-3'}


@pytest.mark.ckan_config('ckan.plugins', 'unaids scheming_datasets')
@pytest.mark.usefixtures('with_plugins')
class TestPackageCreate():

    def test_should_complain_with_exception_when_dataset_type_invalid(self):
        organization = factories.Organization()
        exception_message = "Type 'baad-type' is invalid, valid types are"
        with pytest.raises(toolkit.ValidationError, match=exception_message):
            call_action(
                'package_create',
                name="some-name",
                type="baad-type",
                owner_org=organization['name'],
                title="Dataset with missing title"
            )

    def test_create_dataset_without_type_creates_one_with_default_type_of_dataset(self):
        organization = factories.Organization()
        dataset = call_action(
            'package_create',
            name="some-name",
            owner_org=organization['name'],
            title="Dataset without type"
        )

        assert dataset["type"] == "dataset"

    def test_create_dataset_with_valid_type(self):
        organization = factories.Organization()
        dataset = call_action(
            'package_create',
            name="some-name",
            type="test-schema",
            title="Dataset with valid type",
            owner_org=organization['name']
        )

        assert dataset["type"] == "test-schema"
