import logging
import ckan.plugins.toolkit as toolkit
from flask import Blueprint

log = logging.getLogger(__name__)

login_register_catch = Blueprint(
    u'login_register_catch',
    __name__
)


def disable_default_login():
    '''
    Override and redirect default Login route
    '''
    return toolkit.redirect_to('/user/saml2login')


def disable_default_register():
    '''
    Override and redirect default Register route
    '''
    return toolkit.redirect_to('/user/saml2login')

login_register_catch.add_url_rule(
    u'/user/login', view_func=disable_default_login)
login_register_catch.add_url_rule(
    u'/user/register', view_func=disable_default_register)
