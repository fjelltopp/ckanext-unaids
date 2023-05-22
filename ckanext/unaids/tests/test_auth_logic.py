from unittest.mock import patch

from jose import jwt
import pytest

from ckan.common import g
from ckan.common import request
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
    def test_should_set_user_when_token_correct_and_user_authorized(self, find_user_by_saml_id,
                                                                    validate_and_decode_token):
        token_from_request = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6I"
        request.headers = {"Authorization": token_from_request}
        user_id = "auth0|2fds21gfadsfj3"
        token = {"sub": user_id, "scope": "access:adr email"}
        validate_and_decode_token.return_value = token
        user = User()
        find_user_by_saml_id.return_value = user
        with pytest.raises(AttributeError, match="'_Globals' object has no attribute 'userobj'"):
            g.userobj

        assert auth_logic.access_token_present_and_valid_and_user_authorized()
        assert g.userobj == user
        assert g.user == "Some name"
        find_user_by_saml_id.assert_called_once_with(user_id)
        validate_and_decode_token.assert_called_once_with(token_from_request)

    def test_should_return_false_when_no_token(self):
        request.headers = {}

        assert not auth_logic.access_token_present_and_valid_and_user_authorized()

    @patch('ckanext.unaids.auth_logic.validate_and_decode_token')
    def test_should_throw_when_subject_of_different_origin_than_auth0(self, validate_and_decode_token):
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
                           match="User 'auth0|497d989fd03090s' has not yet logged into ADR"):
            auth_logic.find_user_by_saml_id(subject)

    @patch('ckanext.unaids.auth_logic.Session')
    def test_should_throw_when_multiple_users_found(self, session):
        session.query.return_value.filter.return_value.all.return_value = [User(), User()]

        subject = "auth0|497d989fd03090sa"

        with pytest.raises(auth_logic.OAuth2AuthorizationError,
                           match="User 'auth0|497d989fd03090s' has more than 1 account, please remove unused accounts"):
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


@pytest.mark.ckan_config('ckan.plugins', 'unaids')
@pytest.mark.usefixtures('with_request_context', 'with_plugins')
class TestValidateAndDecodeToken(object):
    @patch('ckanext.unaids.auth_logic.jwt.decode')
    @patch('ckanext.unaids.auth_logic.jwt.get_unverified_header')
    @patch('json.loads')
    @patch('ckanext.unaids.auth_logic.urlopen')
    def test_should_validate_and_decode_token(self, urlopen, loads, get_unverified_header, decode):
        token = "eyJhbGciOiJSUzI1NiIsInR5cCI6Ik"
        encoded = f"Bearer {token}"
        payload = {"name": "somename"}
        jsonurl_read = "jsonurl.read"
        urlopen.return_value.read.return_value = jsonurl_read
        key_c = {
            "kid": "key_c",
            "kty": "kty_c",
            "use": "use_c",
            "n": "n_c",
            "e": "e_c"
        }
        loads.return_value = {
            "keys": [{
                "kid": "key_a"
            }, {
                "kid": "key_b"
            }, key_c]
        }
        decode.return_value = payload
        get_unverified_header.return_value = {"kid": "key_c"}

        decoded_token = auth_logic.validate_and_decode_token(encoded)

        assert decoded_token == payload
        urlopen.assert_called_once_with("https://unittests.org/.well-known/jwks.json")
        loads.assert_called_once_with(jsonurl_read)
        get_unverified_header.assert_called_once_with(token)
        decode.assert_called_once_with(token, key_c, algorithms=["RS256"], audience="http://api.unittests.org",
                                       issuer="https://unittests.org/")

    @patch('ckanext.unaids.auth_logic.jwt.get_unverified_header')
    @patch('json.loads')
    @patch('ckanext.unaids.auth_logic.urlopen')
    def test_should_throw_when_no_matching_rsa_key(self, urlopen, loads, get_unverified_header):
        encoded = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6Ik"
        urlopen.return_value.read.return_value = "jsonurl.read"
        loads.return_value = {
            "keys": [{
                "kid": "key_a"
            }, {
                "kid": "key_b"
            }, {
                "kid": "key_c"
            }]
        }
        get_unverified_header.return_value = {"kid": "key_d"}

        with pytest.raises(auth_logic.OAuth2AuthenticationError,
                           match="Unable to find appropriate key"):
            auth_logic.validate_and_decode_token(encoded)

    @patch('ckanext.unaids.auth_logic.jwt.decode')
    @patch('ckanext.unaids.auth_logic.jwt.get_unverified_header')
    @patch('json.loads')
    @patch('ckanext.unaids.auth_logic.urlopen')
    def test_should_throw_when_token_expired(self, urlopen, loads, get_unverified_header, decode):
        token = "eyJhbGciOiJSUzI1NiIsInR5cCI6Ik"
        encoded = f"Bearer {token}"
        jsonurl_read = "jsonurl.read"
        urlopen.return_value.read.return_value = jsonurl_read
        key_c = {
            "kid": "key_c",
            "kty": "kty_c",
            "use": "use_c",
            "n": "n_c",
            "e": "e_c"
        }
        loads.return_value = {
            "keys": [{
                "kid": "key_a"
            }, {
                "kid": "key_b"
            }, key_c]
        }
        decode.side_effect = jwt.ExpiredSignatureError
        get_unverified_header.return_value = {"kid": "key_c"}

        with pytest.raises(auth_logic.OAuth2AuthenticationError,
                           match="Token is expired"):
            auth_logic.validate_and_decode_token(encoded)

    @patch('ckanext.unaids.auth_logic.log')
    @patch('ckanext.unaids.auth_logic.jwt.decode')
    @patch('ckanext.unaids.auth_logic.jwt.get_unverified_header')
    @patch('json.loads')
    @patch('ckanext.unaids.auth_logic.urlopen')
    def test_should_throw_when_incorrect_claims(self, urlopen, loads, get_unverified_header, decode, log):
        encoded = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6Ik"
        jsonurl_read = "jsonurl.read"
        urlopen.return_value.read.return_value = jsonurl_read
        key_c = {
            "kid": "key_c",
            "kty": "kty_c",
            "use": "use_c",
            "n": "n_c",
            "e": "e_c"
        }
        loads.return_value = {
            "keys": [{
                "kid": "key_a"
            }, {
                "kid": "key_b"
            }, key_c]
        }
        decode.side_effect = jwt.JWTClaimsError("something")
        get_unverified_header.return_value = {"kid": "key_c"}

        with pytest.raises(auth_logic.OAuth2AuthenticationError,
                           match="Incorrect claims, please check the audience and issuer."):
            auth_logic.validate_and_decode_token(encoded)

        log.debug.assert_called_once_with(
            "Incorrect claims, expected audience: http://api.unittests.org, original error: something")

    @patch('ckanext.unaids.auth_logic.jwt.decode')
    @patch('ckanext.unaids.auth_logic.jwt.get_unverified_header')
    @patch('json.loads')
    @patch('ckanext.unaids.auth_logic.urlopen')
    def test_should_throw_when_general_exception_thrown(self, urlopen, loads, get_unverified_header, decode):
        encoded = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6Ik"
        jsonurl_read = "jsonurl.read"
        urlopen.return_value.read.return_value = jsonurl_read
        key_c = {
            "kid": "key_c",
            "kty": "kty_c",
            "use": "use_c",
            "n": "n_c",
            "e": "e_c"
        }
        loads.return_value = {
            "keys": [{
                "kid": "key_a"
            }, {
                "kid": "key_b"
            }, key_c]
        }
        decode.side_effect = Exception
        get_unverified_header.return_value = {"kid": "key_c"}

        with pytest.raises(auth_logic.OAuth2AuthenticationError,
                           match="Unable to parse authentication token"):
            auth_logic.validate_and_decode_token(encoded)


class User:
    name = "Some name"
