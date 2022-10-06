# encoding: utf-8
import logging
import ckan.lib.helpers as h
from flask import Blueprint
from ckan.common import g
from ckan.plugins import toolkit
from ckanext.unaids.custom_user_profile import validate_plugin_extras_provided

log = logging.getLogger(__name__)

validate_user_profile = Blueprint(
    'validate_user_profile',
    __name__,
)


def check_user_affiliation():
    """
    Check if user profile has the custom fields, as defined by this plugin.
    """
    try:
        user_profile = g.userobj
    except Exception:
        h.redirect_to(u'user.login')

    try:
        user_profile_dict = user_profile.as_dict()
        plugin_extras = user_profile_dict.get('plugin_extras', {})
        unaids_extras = plugin_extras.get('unaids', {})
        validate_plugin_extras_provided(unaids_extras)
    except (toolkit.ValidationError, AttributeError):
        # if validation fails or extra fields do not exist (AttributeError; e.g. user created before this extension)
        # then redirect to the user profile page with a flash error so the user know what to do
        h.flash_error(
            "UNAIDS requests that further information be added "
            "to your user profile. Please complete the required "
            "fields below before continuing..."
        )
        return h.redirect_to(u'user.edit')

    # if this passes fine then carry on as normal (i.e. load the dashboard)
    # Note - this now ignores the ckan.route_after_login config setting, which is not ideal
    return h.redirect_to('dashboard.index')


validate_user_profile.add_url_rule(
    "/",
    view_func=check_user_affiliation,
    methods=['GET']
)
