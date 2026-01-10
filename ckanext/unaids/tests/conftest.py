import pytest

from ckan import model
from ckan.tests import factories
from ckanext.unaids.tests import unaids_db_setup, create_version
from ckanext.versions.tests import versions_db_setup
from ckanext.validation.model import tables_exist, create_tables
from ckanext.ytp_request.tests import ytp_request_db_setup


# SQL for creating ckanext_pages table (from ckanext-pages migrations)
# This is needed because clean_db wipes the database and migrate_db_for("pages")
# requires the pages plugin to be loaded, but fixtures run before plugin markers
CKANEXT_PAGES_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ckanext_pages (
    id TEXT PRIMARY KEY,
    title TEXT DEFAULT '',
    name TEXT DEFAULT '',
    content TEXT DEFAULT '',
    lang TEXT DEFAULT '',
    "order" TEXT DEFAULT '',
    private BOOLEAN DEFAULT TRUE,
    group_id TEXT DEFAULT NULL,
    user_id TEXT DEFAULT '',
    publish_date TIMESTAMP,
    page_type TEXT,
    created TIMESTAMP,
    modified TIMESTAMP,
    extras TEXT DEFAULT '{}',
    revisions JSONB
);
"""


@pytest.fixture
def clean_db_with_migrations(clean_db):
    """
    Extends clean_db to add CKAN 2.11 plugin migrations.

    The clean_db fixture rebuilds the database fresh for test isolation,
    which wipes out plugin migrations. This fixture adds:
    - permission_labels column required by CKAN 2.11 activity plugin
    - ckanext_pages table required by ckanext-pages plugin

    Note: We use SQL instead of migrate_db_for() because the pages plugin
    isn't loaded when fixtures run (fixtures execute before test markers).
    """
    # Add permission_labels column to activity table (required by CKAN 2.11 activity plugin)
    model.Session.execute(
        "ALTER TABLE activity ADD COLUMN IF NOT EXISTS permission_labels text[]"
    )
    # Create ckanext_pages table (required by ckanext-pages plugin)
    model.Session.execute(CKANEXT_PAGES_TABLE_SQL)
    model.Session.commit()


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
