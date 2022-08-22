# encoding: utf-8
import logging
import ckan.lib.helpers as h
from flask import Blueprint
from operator import index
from ckan.common import _, config, g
from ckan.plugins import toolkit
from ckan.views.dashboard import index
from ckanext.unaids.actions import check_plugin_extras_provided

log = logging.getLogger(__name__)

user_affiliation = Blueprint(
    'useraffiliation',
    __name__,
)


def check_user_affiliation():
    """
    Check if user profile has the custom fields, as defined by this plugin.
    """
    try:
        # get user profile
        user_profile = g.userobj
    except:
        # assume if this fails that the user is not logged in?
        h.redirect_to(u'user.login')

    try:
        # does user have the new fields and are they non-empty strings
        check_plugin_extras_provided(user_profile.plugin_extras.get('useraffiliation'))
        # if this passes fine then carry on as normal (i.e. load the dashboard)
        # Note - this now ignores the ckan.route_after_login config setting, which is not ideal
        return index()
        
    except toolkit.ValidationError as e:
        # if this fails then redirect to the user profile page
        # with a flash error so the user know what to do
        h.flash_error('Please complete your profile by completing the required fields.')
        return h.redirect_to(u'user.edit')


def get_route_to_intercept():
    """
    Get the route that should be intercepted
    """
    configured_route = config.get('ckan.route_after_login', 'dashboard.index')

    # the default is dashboard.index
    # however, and ".index"es will not get caught at, for example, "/dashboard/"
    # so we remove any ending ".index"
    if configured_route.endswith('.index'):
        configured_route = configured_route[:-6]
        
    # add the leading and trailing slashes
    # and convert any internal periods to slashes
    return '/' + configured_route.replace('.', '/') + '/'

user_affiliation.add_url_rule(
    get_route_to_intercept(),
    view_func=check_user_affiliation,
    methods=['GET']
)
