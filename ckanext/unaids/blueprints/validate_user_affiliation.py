# encoding: utf-8
import logging
import ckan.lib.helpers as h
from flask import Blueprint
from ckan.common import g, _
from ckan.plugins import toolkit
from ckanext.unaids import helpers
from ckanext.unaids.custom_user_profile import validate_plugin_extras_provided

log = logging.getLogger(__name__)

validate_user_affiliation = Blueprint(
    'validate_user_affiliation',
    __name__,
    url_prefix = '/validate-user-affiliation'
)


@validate_user_affiliation.route('/')
def check_user_affiliation():
    """
    Check if user profile has the custom fields, as defined by this plugin.
    """
    try:
        user_profile = g.userobj
    except Exception:
        return h.redirect_to(controller='saml2auth', action='saml2login', id=None, came_from="/validate-user-affiliation/")

    try:
        user_profile_dict = user_profile.as_dict()
        plugin_extras = user_profile_dict.get('plugin_extras', {})
        unaids_extras = plugin_extras.get('unaids', {})
        validate_plugin_extras_provided(unaids_extras)
    except (toolkit.ValidationError, AttributeError):
        return h.redirect_to(helpers.get_profile_editor_url(
            after_save_url=h.url_for("validate_user_affiliation.success_callback", _external=True),
            back_url=h.url_for('dashboard.index', _external=True),
            flash_message=_("UNAIDS asks that further information be added "
            "to your user profile. Please complete the required "
            "fields missing below before continuing...")
        ))

    return h.redirect_to('dashboard.index')

@validate_user_affiliation.route('/success-callback/')
def success_callback():
    h.flash_success(
        _("Thank you for updating your profile information.")
    )
    return h.redirect_to('dashboard.index')
