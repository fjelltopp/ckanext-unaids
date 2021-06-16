import pytest

from ckanext.unaids.tests import unaids_db_setup
from ckanext.validation.tests import validation_db_setup
from ckanext.versions.tests import versions_db_setup


@pytest.fixture(autouse=True)
def unaids_setup(clean_db):
    validation_db_setup()
    versions_db_setup()
    unaids_db_setup()
