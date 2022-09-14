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


def _check_user_affiliation():
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
        plugin_extras_dict = user_profile.as_dict().get('plugin_extras',{})
        if plugin_extras_dict is None or plugin_extras_dict.get('useraffiliation') is None:
            # this should catch users created before this extension was created
            log.info('Redirecting user to the profile edit page as no affiliation data found (1)')
            h.flash_error('Please complete your profile by completing the required fields.')
            return h.redirect_to(u'user.edit')
        else:
            check_plugin_extras_provided(plugin_extras_dict.get('useraffiliation',{}))
            # if this passes fine then carry on as normal (i.e. load the dashboard)
            # Note - this now ignores the ckan.route_after_login config setting, which is not ideal
            return index()
        
    except toolkit.ValidationError as e:
        # if validation fails then redirect to the user profile page
        # with a flash error so the user know what to do
        # this will be when either field is an empty string
        log.info('Redirecting user to the profile edit page as no affiliation data found (2)')
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
    view_func=_check_user_affiliation,
    methods=['GET']
)
