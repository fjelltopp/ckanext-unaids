# coding: utf
import ckan.logic as logic


def organization_update_access(context, data_dict=None):
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
