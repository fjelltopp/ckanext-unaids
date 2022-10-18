# encoding: utf-8
import logging
import ckan.lib.helpers as h
from flask import Blueprint
from flask.views import MethodView
from ckan import model
from ckan.common import g
from ckan.plugins import toolkit
from ckanext.unaids.custom_user_profile import validate_plugin_extras_provided

log = logging.getLogger(__name__)

validate_user_profile = Blueprint(
    'validate_user_profile',
    __name__,
)

class EditUserAffiliationView(MethodView):
    @staticmethod
    def _get_context():
        # TODO: confirm all of these fields are needed
        return {
            'model': model,
            'session': model.Session,
            'user': toolkit.c.user,
            'for_view': True,
            'auth_user_obj': toolkit.c.userobj
        }

    def post(self, id=None):
        context = self._get_context()
        try:
            user_profile = g.userobj
        except Exception:
            h.redirect_to('user.login')


        try:
            user_profile_dict = user_profile.as_dict()

            user_profile_dict['job_title'] = toolkit.request.form['job_title']
            user_profile_dict['affiliation'] = toolkit.request.form['affiliation']
            
            toolkit.get_action('user_update')(context, user_profile_dict)
            
            h.flash_success('Profile updated')
            return h.redirect_to('dashboard.index')

        except toolkit.ValidationError as e:
            errors = e.error_dict
            error_summary = e.error_summary

            return self.get(id, toolkit.request.form, errors, error_summary)

    def get(self,
            id=None,
            data=None,
            errors=None,
            error_summary=None):

        user_profile = g.userobj
        user_profile_dict = user_profile.as_dict()
        
        if data is None:
            plugin_extras = user_profile_dict.get('plugin_extras', {})
            data = plugin_extras.get('unaids', {})

        errors = errors or {}
        vars = {
            'data': data,
            'errors': errors,
            'error_summary': error_summary or None,
        }

        extra_vars = {
            'user_dict': user_profile_dict,
        }

        vars.update(extra_vars)
        extra_vars['form'] = toolkit.render(
            'user/edit_user_affiliation_form.html',
            extra_vars=vars)

        return toolkit.render('user/edit.html', extra_vars)

def check_user_affiliation():
    """
    Check if user profile has the custom fields, as defined by this plugin.
    """
    try:
        user_profile = g.userobj
    except Exception:
        h.redirect_to('user.login')

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

        return h.redirect_to('/edit_user_affiliation')

    # if this passes fine then carry on as normal (i.e. load the dashboard)
    # Note - this now ignores the ckan.route_after_login config setting, which is not ideal
    return h.redirect_to('dashboard.index')


validate_user_profile.add_url_rule(
    "/check_user_affiliation",
    view_func=check_user_affiliation,
    methods=['GET']
)
validate_user_profile.add_url_rule(
    '/edit_user_affiliation',
    view_func=EditUserAffiliationView.as_view('edit_user_affiliation'),
    methods=['GET','POST']
)
