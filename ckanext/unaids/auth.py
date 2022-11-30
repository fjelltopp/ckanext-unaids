# coding: utf
import ckan.logic as logic
import ckan.model as model
import ckan.plugins.toolkit as toolkit


def unaids_organization_update(context, data_dict=None):
    user_organizations = \
        logic.get_action('organization_list_for_user')(
            {'user': context['user']}, {}
        )
    valid = str(data_dict['id']) in [
        str(org['id'])
        for org in user_organizations
        if org['capacity'] in ['admin', 'editor']
    ]
    if valid:
        return {'success': True}
    else:
        return {
            'success': False,
            'msg': 'You cannot carry out this action'
        }


def substitute_user(substitute_user_id):
    substitute_user_obj = model.User.get(substitute_user_id)

    if not substitute_user_obj:
        return {
            "success": False,
            "error": {
                "__type": "Bad Request",
                "message": "CKAN-Substitute-User header does not "
                           "identify a valid CKAN user"
            }
        }, 400

    toolkit.g.user = substitute_user_obj.name
    toolkit.g.userobj = substitute_user_obj
