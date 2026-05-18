import pytest
import ckan.plugins as p

from ckan.tests import factories
from ckanext.unaids.tests import unaids_db_setup, create_version
from ckanext.versions.tests import versions_db_setup
from ckanext.validation.model import tables_exist, create_tables
from ckanext.ytp_request.tests import ytp_request_db_setup


@pytest.fixture
def clean_db_with_migrations(clean_db, with_plugins, migrate_db_for):
    # CKAN 2.11: clean_db rebuilds the core schema only. Plugin-owned tables
    # (activity.permission_labels as text[], ckanext_pages) need their Alembic
    # migrations re-applied. Only migrate plugins actually loaded for this test
    # so test classes don't need to declare plugins they don't use.
    for plugin_name in ("activity", "pages"):
        if p.plugin_loaded(plugin_name):
            migrate_db_for(plugin_name)


@pytest.fixture(autouse=True)
def unaids_setup(clean_db_with_migrations):
    if not tables_exist():
        create_tables()

    versions_db_setup()
    ytp_request_db_setup()
    unaids_db_setup()


@pytest.fixture()
def org_admin():
    return factories.User(name="admin")


@pytest.fixture()
def org_editor():
    return factories.User(name="editor")


@pytest.fixture()
def org_member():
    return factories.User(name="member")


@pytest.fixture()
def test_organization(org_admin, org_editor, org_member):
    return factories.Organization(users=[
        {'name': org_admin['id'], 'capacity': 'admin'},
        {'name': org_editor['id'], 'capacity': 'editor'},
        {'name': org_member['id'], 'capacity': 'member'}
    ])


@pytest.fixture()
def test_dataset(test_organization):
    return factories.Dataset(owner_org=test_organization['id'])


@pytest.fixture()
def test_resource(test_dataset):
    return factories.Resource(package_id=test_dataset['id'])


@pytest.fixture()
def test_version(test_dataset, org_editor):
    return create_version(test_dataset['id'], org_editor, version_name="Version1")
