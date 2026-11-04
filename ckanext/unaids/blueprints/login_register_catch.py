import logging
import ckan.plugins.toolkit as toolkit
from flask import Blueprint

log = logging.getLogger(__name__)

login_register_catch = Blueprint("login_register_catch", __name__)


def disable_default_login_register():
    """
    Override and redirect default Login route
    """
    return toolkit.redirect_to("/user/saml2login")


# Leave CKAN's own login/register routes alone when internal login is enabled
# (e.g. local development without access to the SAML IdP).
if not toolkit.asbool(toolkit.config.get("ckanext.saml2auth.enable_ckan_internal_login")):
    login_register_catch.add_url_rule("/user/login", view_func=disable_default_login_register)
    login_register_catch.add_url_rule("/user/register", view_func=disable_default_login_register)
