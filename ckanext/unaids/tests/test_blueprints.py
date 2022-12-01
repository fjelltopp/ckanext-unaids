"""Tests for plugin.py."""
import logging
import pytest

log = logging.getLogger(__name__)


@pytest.mark.ckan_config("ckan.plugins", "unaids pages")
@pytest.mark.usefixtures("with_plugins")
class TestValidateUserProfileBlueprint(object):
    def test_annonymous_access_to_index_page(self, app):
        index_response = app.get("/", follow_redirects=False)
        assert index_response.status_code == 200
