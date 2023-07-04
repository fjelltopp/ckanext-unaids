import pytest

from ckanext.unaids.helpers import url_is_edit_url_for_username


@pytest.mark.parametrize("url,found",
                         [
                             ("/user/edit/admin", True),
                             ("/user/edit/admin_fjelltopp", False),
                             ("/user/edit/admin/something?key=value", True),
                             ("/user/edit/admin?something", True),
                             ("/user/edit/admin/", True),
                             ("/user/edit/administr/", False),
                             ("http://ape.ft.com/user/edit/admin", True),
                             ("http://ape.ft.com/user/edit/adminitration", False)
                         ])
def test_finding_user_name(url, found):
    assert url_is_edit_url_for_username(url, "admin") == found
