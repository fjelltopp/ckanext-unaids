import ckan.lib.navl.dictization_functions as df
import ckan.plugins.toolkit as toolkit
from ckan.common import _


def if_empty_guess_format(key, data, errors, context):
    """
    Overrides the core if_empty_guess_format validator to add the geojson & pjnz
    file types to those that it guesses.
    """
    value = data[key]
    resource_id = data.get(key[:-1] + ('id',))
    # if resource_id then an update
    if (not value or value is df.Missing) and not resource_id:
        url = data.get(key[:-1] + ('url',), '')
        response = toolkit.get_action('format_guess')(context, {'filename': url})
        if response.get('mimetype'):
            data[key] = response['mimetype']


def organization_id_exists_validator(key, data, errors, context):
    """
    Make sure an field is a valid organization_id
    """
    value = data.get(key)
    if value:
        all_organizaions = toolkit.get_action('organization_list')(
            {}, {'all_fields': True}
        )
        is_valid = value in [
            x['id']
            for x in all_organizaions
        ]
        if not is_valid:
            raise df.Invalid(_('Invalid organization'))


def read_only(key, data, errors, context):
    bypass_read_only = context.get('bypass_read_only', False)
    if bypass_read_only:
        return
    if context.get('package', False):
        old_locked_status = context.get('package', {}).get('locked', False)
        if data[key] != old_locked_status:
            raise toolkit.Invalid(
                f'Cannot change value of "{key[-1]}" from {old_locked_status}'
                f' to {data[key]}. This key is read-only'
            )
    else:
        raise toolkit.Invalid(
            f'Cannot set value of "{key[-1]}" to {data[key]}. This key is read-only.'
        )
