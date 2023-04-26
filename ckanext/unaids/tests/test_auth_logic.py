from ckan.common import g

from unittest.mock import patch
from ckan.common import request

import pytest
import ckanext.unaids.auth_logic as auth_logic


@pytest.mark.parametrize("status,headers,expected ", [
    ("401 ", {}, True),
    ("401 ", {"Content-Type": "text/html"}, True),
    ("401 ", {"Content-Type": "text/json"}, False),
    ("404 ", {}, False),
    ("404 ", {"Content-Type": "text/html"}, False),
    ("404 ", {"Content-Type": "text/json"}, False)
])
def test_json_response_omitting_challenge_decider(status, headers, expected):
    assert auth_logic.json_response_omitting_challenge_decider(None, status, headers) == expected


class TestExtractToken(object):
    def test_should_pass_when_right_token(self):
        assert auth_logic.extract_token("Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6I") == "eyJhbGciOiJSUzI1NiIsInR5cCI6I"

    def test_should_throw_when_not_bearer(self):
        with pytest.raises(auth_logic.OAuth2AuthenticationError, match="Authorization header must start with Bearer"):
            auth_logic.extract_token("User")

    def test_should_throw_when_more_than_2_parts(self):
        with pytest.raises(auth_logic.OAuth2AuthenticationError, match="Authorization header must be Bearer token"):
            auth_logic.extract_token("Bearer ey2323 ddd")

    def test_should_throw_when_no_token_present(self):
        with pytest.raises(auth_logic.OAuth2AuthenticationError, match="Token not found"):
            auth_logic.extract_token("Bearer")


@pytest.mark.ckan_config('ckan.plugins', 'unaids')
@pytest.mark.usefixtures('with_plugins')
class TestVerifyRequiredScope(object):

    def test_should_pass_when_scope_is_right(self):
        token = {'scope': 'access:adr'}

        auth_logic.verify_required_scope(token)

    def test_should_complain_when_scope_is_none(self):
        token = {'scope': ''}

        with pytest.raises(auth_logic.OAuth2AuthorizationError, match="Invalid scope. Required: 'access:adr'"):
            auth_logic.verify_required_scope(token)

    def test_should_complain_when_scope_is_incorrect(self):
        token = {'scope': 'email openid calendar:write'}

        with pytest.raises(auth_logic.OAuth2AuthorizationError, match="Invalid scope. Required: 'access:adr'"):
            auth_logic.verify_required_scope(token)

@pytest.mark.ckan_config('ckan.plugins', 'unaids')
@pytest.mark.usefixtures('with_request_context', 'with_plugins')
class TestAccessTokenPresentAndValidAndUserAuthorized():

    @patch('ckanext.unaids.auth_logic.validate_and_decode_token')
    @patch('ckanext.unaids.auth_logic.find_user_by_saml_id')
    def test_should_set_user_when_token_correct_and_user_authorized(self, find_user_by_saml_id, validate_and_decode_token):
        request.headers = {"Authorization": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6I"}
        token = {"sub": "auth0|2fds21gfadsfj3", "scope": "access:adr email"}
        validate_and_decode_token.return_value = token
        user = User()
        find_user_by_saml_id.return_value = user
        with pytest.raises(AttributeError, match="'_Globals' object has no attribute 'userobj'"):
            g.userobj

        assert auth_logic.access_token_present_and_valid_and_user_authorized()
        assert g.userobj == user
        assert g.user == "Some name"


    @patch('ckanext.unaids.auth_logic.validate_and_decode_token')
    @patch('ckanext.unaids.auth_logic.find_user_by_saml_id')
    def test_should_return_false_when_no_token(self, find_user_by_saml_id, validate_and_decode_token):
        request.headers = {}

        assert not auth_logic.access_token_present_and_valid_and_user_authorized()

    @patch('ckanext.unaids.auth_logic.validate_and_decode_token')
    @patch('ckanext.unaids.auth_logic.find_user_by_saml_id')
    def test_should_throw_when_subject_of_different_origin_than_auth0(self, find_user_by_saml_id, validate_and_decode_token):
        request.headers = {"Authorization": "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6I"}
        token = {"sub": "google-oauth2|larry.page@gmail.com", "scope": "access:adr email"}
        validate_and_decode_token.return_value = token

        with pytest.raises(auth_logic.OAuth2AuthenticationError,
                           match="Only auth0 identity provider is supported, got 'google-oauth2|larry.page@gmail.com'"):
            auth_logic.access_token_present_and_valid_and_user_authorized()


class User:
    name = "Some name"
