import pytest
import ckanext.unaids.auth_logic as auth_logic


@pytest.mark.parametrize("status,headers,expected ", [
    ("401 ", {}, True),
    ("401 ", {"Content-Type": "text/html"}, True),
    ("401 ", {"Content-Type": "text/json"}, False),
    ("404 ", {}, False),
    ("404 ", {"Content-Type": "text/html"}, False),
    ("404 ", {"Content-Type": "text/json"}, False)
], )
def test_json_response_omitting_challenge_decider(status, headers, expected):
    assert auth_logic.json_response_omitting_challenge_decider(None, status, headers) == expected


