# coding: utf
import ckan.model as model
import ckan.plugins.toolkit as toolkit


def dataset_lock(context, data_dict):
    # Sysadmins only
    return {
        'success': False,
        'msg': 'You cannot carry out this action'
    }


@toolkit.chained_auth_function
@toolkit.auth_sysadmins_check
def package_update(next_auth_action, context, data_dict):
    result = next_auth_action(context, data_dict)
    locked = toolkit.asbool(context['package'].extras.get("locked", 'false'))
    if locked:
        return {
            'success': False,
            'msg': ('Dataset must first be unlocked by a sysadmin.')
        }
    else:
        return result


def unaids_organization_update(context, data_dict=None):
    user_organizations = \
        toolkit.get_action('organization_list_for_user')(
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
