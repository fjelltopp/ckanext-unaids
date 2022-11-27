# encoding: utf-8
import logging
from ckan.common import g, _
from ckan.lib import helpers as h
from ckan.logic import get_action
from ckan.views.user import before_request
from six import ensure_str
import dominate.tags as dom_tags
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
        return h.redirect_to(locale=locale, controller='saml2auth', action='saml2login',
                             id=None, came_from="/me")
    else:
        context = None
        data_dict = {'id': g.user}

        user_dict = get_action('user_show')(context, data_dict)
        apikey = user_dict['apikey']
        copy_btn = dom_tags.button(dom_tags.i(u'', {
            u'class': u'fa fa-copy'
        }), {
            u'type': u'button',
            u'class': u'btn btn-default btn-xs',
            u'data-module': u'copy-into-buffer',
            u'data-module-copy-value': ensure_str(apikey)
        })
        h.flash_success(
            _('Your api key is: '
              '<code style=\"word-break:break-all;\"> {token}</code> {copy}'
              ).format(token=apikey, copy=copy_btn),
            allow_html=True
        )
        return h.redirect_to(locale=locale, controller='user', action='read', id=g.user)


user_info_blueprint.add_url_rule(
    u'',
    view_func=display_user_details,
    strict_slashes=False
)
