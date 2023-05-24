import logging
import json

from ckantoolkit import config
from repoze.who.interfaces import IChallengeDecider
from six.moves.urllib.request import urlopen
from flask import _request_ctx_stack, Response
from jose import jwt
from zope.interface import directlyProvides

from ckan.common import request, g
from ckan.logic import ActionError
from ckan.model import Session, User

AUTH0_DOMAIN = config.get('ckanext.unaids.auth0_domain')
API_AUDIENCE = config.get('ckanext.unaids.oauth2_api_audience')
REQUIRED_SCOPE = config.get('ckanext.unaids.oauth2_required_scope')
ALGORITHMS = ["RS256"]

log = logging.getLogger()


class OAuth2AuthenticationError(ActionError):
    pass


class OAuth2AuthorizationError(ActionError):
    pass


def json_response_omitting_challenge_decider(environ, status, headers):
    h_dict = dict(headers)
    ct = h_dict.get('Content-Type')
    if ct is not None:
        return not ct.startswith('text/json') and status.startswith('401 ')

    return status.startswith('401 ')


directlyProvides(json_response_omitting_challenge_decider, IChallengeDecider)


# based on work from https://auth0.com/docs/quickstart/backend/python/01-authorization
def access_token_present_and_valid_and_user_authorized():
    token = request.headers.get('Authorization', '')
    if token and token.startswith("Bearer "):
        access_token = validate_and_decode_token(token)
        verify_required_scope(access_token)
        subject = access_token['sub']

        if not subject.startswith("auth0|"):
            raise OAuth2AuthenticationError(message=f"Only auth0 identity provider is supported, got '{subject}'")

        user = find_user_by_saml_id(subject)
        g.userobj = user
        g.user = user.name

        return True

    return False


def validate_and_decode_token(encoded):
    token = extract_token(encoded)
    jsonurl = urlopen("https://" + AUTH0_DOMAIN + "/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())
    unverified_header = jwt.get_unverified_header(token)
    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == unverified_header["kid"]:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"]
            }
    if rsa_key:
        try:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=ALGORITHMS,
                audience=API_AUDIENCE,
                issuer="https://" + AUTH0_DOMAIN + "/"
            )
        except jwt.ExpiredSignatureError:
            raise OAuth2AuthenticationError(message="Token is expired")
        except jwt.JWTClaimsError as e:
            log.debug(f"Incorrect claims, expected audience: {API_AUDIENCE}, original error: {e}")
            raise OAuth2AuthenticationError(message="Incorrect claims, please check the audience and issuer.")
        except Exception:
            raise OAuth2AuthenticationError(message="Unable to parse authentication token")

        _request_ctx_stack.top.current_user = payload
        return payload
    raise OAuth2AuthenticationError(message="Unable to find appropriate key")


def extract_token(encoded_token):
    """Obtains the Access Token from the Authorization Header
    """
    parts = encoded_token.split()

    if len(parts) == 1:
        raise OAuth2AuthenticationError(message="Token not found")
    elif len(parts) > 2:
        raise OAuth2AuthenticationError(message="Authorization header must be Bearer token")

    token = parts[1]
    return token


def verify_required_scope(token):
    required_scope = config.get("ckanext.unaids.oauth2_required_scope")

    if token.get("scope"):
        token_scopes = token["scope"].split()
        for token_scope in token_scopes:
            if token_scope == required_scope:
                return

    raise OAuth2AuthorizationError(message=f"Invalid scope. Required: '{required_scope}'")


def find_user_by_saml_id(subject):
    users = Session.query(User).filter(
        User.plugin_extras["saml2auth", "saml_id"].astext == subject and User.state == 'active'
    ).all()

    if len(users) == 0:
        raise OAuth2AuthorizationError(message=f"User '{subject}' has not yet logged into ADR")
    elif len(users) > 1:
        raise OAuth2AuthorizationError(
            message=f"User '{subject}' has more than 1 account, please remove unused accounts")

    return users[0]


def create_response(error_type, message, error_code):
    response = {
        "error": {
            "__type": error_type,
            "message": message
        },
        "success": False
    }

    resp = Response(response=json.dumps(response))
    resp.status_code = error_code
    resp.content_type = "text/json"

    return resp
