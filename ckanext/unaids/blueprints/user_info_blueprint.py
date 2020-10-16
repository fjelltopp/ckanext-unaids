# encoding: utf-8
import logging
from ckan.common import g
from ckan.lib import helpers as h
from ckan.logic import get_action
from ckan.views.user import before_request
from flask import Blueprint

log = logging.getLogger(__name__)

user_info_blueprint = Blueprint(
    u'user_info_blueprint',
    __name__,
    url_prefix=u'/me'
)
user_info_blueprint.before_request(before_request)


def display_user_details(locale=None):
    if not g.user:
        return h.redirect_to(locale=locale, controller='user', action='login',
                             id=None, came_from="/me")
    else:
        context = None
        data_dict = {'id': g.user}

        user_dict = get_action('user_show')(context, data_dict)
        h.flash_success("Your api key is: {}".format(user_dict['apikey']))
        return h.redirect_to(locale=locale, controller='user', action='read', id=g.user)


user_info_blueprint.add_url_rule(
    u'',
    view_func=display_user_details,
    strict_slashes=False
)
