import flask.wrappers

from ckan.common import g

from unittest.mock import patch, MagicMock, Mock
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


class TestFindUserBySamlId:

    @patch('ckanext.unaids.auth_logic.Session')
    def test_should_pass_when_user_found(self, session):
        user = User()
        session.query.return_value.filter.return_value.all.return_value = [user]
        subject = "auth0|497d989fd03090sa"

        assert auth_logic.find_user_by_saml_id(subject) == user

    @patch('ckanext.unaids.auth_logic.Session')
    def test_should_throw_when_user_not_found(self, session):
        session.query.return_value.filter.return_value.all.return_value = []

        subject = "auth0|497d989fd03090sa"

        with pytest.raises(auth_logic.OAuth2AuthorizationError,
                           match="User 'auth0|497d989fd03090sa' has not yet logged into ADR"):
            auth_logic.find_user_by_saml_id(subject)

    @patch('ckanext.unaids.auth_logic.Session')
    def test_should_throw_when_multiple_users_found(self, session):
        session.query.return_value.filter.return_value.all.return_value = [User(), User()]

        subject = "auth0|497d989fd03090sa"

        with pytest.raises(auth_logic.OAuth2AuthorizationError,
                           match="User 'auth0|497d989fd03090sa' has more than 1 account, please remove unused accounts"):
            auth_logic.find_user_by_saml_id(subject)


class TestCreateResponse:
    @pytest.mark.parametrize("error_type,message,error_code,expected ", [
        ("Authorization", "Token is expired", 401,
         b'{"error": {"__type": "Authorization", "message": "Token is expired"}, "success": false}'),
        ("Authentication", "User 'User' has not yet logged into ADR", 404,
         b'{"error": {"__type": "Authentication", '
         b'"message": "User \'User\' has not yet logged into ADR"}, "success": false}')
    ])
    def test_should_create_response(self, error_type, message, error_code, expected):
        response = auth_logic.create_response(error_type, message, error_code)

        assert response.status_code == error_code
        assert response.data == expected
        assert response.content_type == "text/json"


class User:
    name = "Some name"
