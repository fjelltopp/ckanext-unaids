
import ckan.plugins.toolkit as toolkit
from flask import Blueprint
from ckan.views.group import *
from ckan.views.group import _check_access, _action, _get_group_template, _guess_group_type


organizations_per_pages = Blueprint("organization_pagination", __name__)


# both of these are needed to override the default ckan group controller
# Method below is copied from ckan/views/group.py with the only change being
# the number of organizations per page
@organizations_per_pages.route('/organization')
@organizations_per_pages.route('/organization/')
def index():
    group_type = "organization"
    extra_vars = {}
    set_org(True)
    page = h.get_page_number(request.params) or 1
    items_per_page = int(config.get(u'ckan.organizations_per_page', 100))

    context = {
        u'model': model,
        u'session': model.Session,
        u'user': g.user,
        u'for_view': True,
        u'with_private': False
    }

    try:
        _check_access(u'site_read', context)
        _check_access(u'group_list', context)
    except NotAuthorized:
        base.abort(403, _(u'Not authorized to see this page'))

    q = request.params.get(u'q', u'')
    sort_by = request.params.get(u'sort')

    g.q = q
    g.sort_by_selected = sort_by

    extra_vars["q"] = q
    extra_vars["sort_by_selected"] = sort_by

    # pass user info to context as needed to view private datasets of
    # orgs correctly
    if g.userobj:
        context['user_id'] = g.userobj.id
        context['user_is_admin'] = g.userobj.sysadmin

    try:
        data_dict_global_results = {
            u'all_fields': False,
            u'q': q,
            u'sort': sort_by,
            u'type': group_type or u'group',
        }
        global_results = _action(u'group_list')(context,
                                                data_dict_global_results)
    except ValidationError as e:
        if e.error_dict and e.error_dict.get(u'message'):
            msg = e.error_dict['message']
        else:
            msg = str(e)
        h.flash_error(msg)
        extra_vars["page"] = h.Page([], 0)
        extra_vars["group_type"] = group_type
        return base.render(
            _get_group_template(u'index_template', group_type), extra_vars)

    data_dict_page_results = {
        u'all_fields': True,
        u'q': q,
        u'sort': sort_by,
        u'type': group_type or u'group',
        u'limit': items_per_page,
        u'offset': items_per_page * (page - 1),
        u'include_extras': True
    }
    page_results = _action(u'group_list')(context, data_dict_page_results)

    extra_vars["page"] = h.Page(
        collection=global_results,
        page=page,
        url=h.pager_url,
        items_per_page=items_per_page, )

    extra_vars["page"].items = page_results
    extra_vars["group_type"] = group_type

    g.page = extra_vars["page"]
    return base.render(
        _get_group_template(u'index_template', group_type), extra_vars)



