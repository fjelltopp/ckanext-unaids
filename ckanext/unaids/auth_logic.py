from ckantoolkit import config
import json
from six.moves.urllib.request import urlopen

from flask import _request_ctx_stack
from jose import jwt

from ckan.logic import ActionError
from ckan.model import Session, User, ApiToken

AUTH0_DOMAIN = config.get('ckanext.unaids.auth0_domain')
API_AUDIENCE = config.get('ckanext.unaids.oauth2_api_audience')
REQUIRED_SCOPE = config.get('ckanext.unaids.oauth2_required_scope')
ALGORITHMS = ["RS256"]


class OAuth2Error(ActionError):
    pass


# based on work from https://auth0.com/docs/quickstart/backend/python/01-authorization
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
            raise OAuth2Error(message="Token is expired")
        except jwt.JWTClaimsError:
            raise OAuth2Error(message="Incorrect claims, please check the audience and issuer")
        except Exception:
            raise OAuth2Error(message="Unable to parse authentication token")

        _request_ctx_stack.top.current_user = payload
        return payload
    raise OAuth2Error(message="Unable to find appropriate key")


def extract_token(encoded_token):
    """Obtains the Access Token from the Authorization Header
    """
    parts = encoded_token.split()

    if parts[0].lower() != "bearer":
        raise OAuth2Error(message="Authorization header must start with Bearer")
    elif len(parts) == 1:
        raise OAuth2Error(message="Token not found")
    elif len(parts) > 2:
        raise OAuth2Error(message="Authorization header must be Bearer token")

    token = parts[1]
    return token


def verify_required_scope(token):
    required_scope = config.get("ckanext.unaids.oauth2_required_scope")

    if token.get("scope"):
        token_scopes = token["scope"].split()
        for token_scope in token_scopes:
            if token_scope == required_scope:
                return

    raise OAuth2Error(message=f"Invalid scope. Required: '{required_scope}'")


def create_new_token(user_id):
    token = ApiToken(user_id=user_id,name='CKAN-Remote')
    Session.add(token)
    Session.commit()

    return token


def get_or_create_ckan_token(decoded_token):
    subject = decoded_token['sub']
    if not subject.startswith("auth0|"):
        raise OAuth2Error(message="Subject claim is not properly defined")

    user = find_user(subject)
    api_tokens = Session.query(ApiToken).filter(
        ApiToken.user_id == user.id
    ).all()

    if len(api_tokens) > 0:
        return api_tokens[0]
    else:
        return create_new_token(user.id)


def find_user(subject):
    users = Session.query(User).filter(
        User.plugin_extras["saml2auth", "saml_id"].astext == subject and User.state == 'active'
    ).all()

    if len(users) == 0:
        raise OAuth2Error(message="User has not yet logged into ADR")
    elif len(users) > 1:
        raise OAuth2Error(message="User has more than 1 account, please remove unused accounts")

    return users[0]
