from ckantoolkit import config
import json
from six.moves.urllib.request import urlopen

from flask import _request_ctx_stack
from jose import jwt

from ckan.model import Session, User, ApiToken

AUTH0_DOMAIN = config.get('ckanext.unaids.auth0_domain')
API_AUDIENCE = config.get('ckanext.unaids.oauth2_api_audience')
REQUIRED_SCOPE = config.get('ckanext.unaids.oauth2_required_scope')
ALGORITHMS = ["RS256"]


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
            raise AuthError({"code": "token_expired",
                             "description": "token is expired"}, 401)
        except jwt.JWTClaimsError:
            raise AuthError({"code": "invalid_claims",
                             "description":
                                 "incorrect claims,"
                                 "please check the audience and issuer"}, 401)
        except Exception:
            raise AuthError({"code": "invalid_header",
                             "description":
                                 "Unable to parse authentication"
                                 " token."}, 401)

        _request_ctx_stack.top.current_user = payload
        return payload
    raise AuthError({"code": "invalid_header",
                     "description": "Unable to find appropriate key"}, 401)


def extract_token(encoded_token):
    """Obtains the Access Token from the Authorization Header
    """
    parts = encoded_token.split()

    if parts[0].lower() != "bearer":
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Authorization header must start with"
                            " Bearer"}, 401)
    elif len(parts) == 1:
        raise AuthError({"code": "invalid_header",
                        "description": "Token not found"}, 401)
    elif len(parts) > 2:
        raise AuthError({"code": "invalid_header",
                        "description":
                            "Authorization header must be"
                            " Bearer token"}, 401)

    token = parts[1]
    return token


class AuthError(Exception):
    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code


def verify_required_scope(token):
    required_scope = config.get("ckanext.unaids.oauth2_required_scope")

    if token.get("scope"):
        token_scopes = token["scope"].split()
        for token_scope in token_scopes:
            if token_scope == required_scope:
                return

    raise AuthError({"code": "invalid_header",
                     "description":
                         f"Invalid scope. Required: '{required_scope}'"}, 401)


def create_new_token(user_id):
    token = ApiToken(user_id=user_id,name='CKAN-Remote')
    Session.add(token)
    Session.commit()

    return token


def get_or_create_ckan_token(decoded_token):
    subject = decoded_token['sub']
    if not subject.startswith("auth0|"):
        raise AuthError({"code": "invalid_header",
                         "description":
                             "Subject is not properly defined"}, 401)

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
        raise AuthError({"code": "invalid_header",
                         "description":
                             "User has not logged into ADR before"}, 401)
    elif len(users) > 1:
        raise AuthError({"code": "invalid_header",
                         "description":
                             "User has more than 1 account, please remove unused accounts"}, 401)

    return users[0]
