import ckan.lib.navl.dictization_functions as df
import ckan.plugins.toolkit as toolkit
from ckanext.scheming.validation import scheming_validator
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


@scheming_validator
def read_only(field, schema):
    default_value = field.get(u'field_value', field.get('default', ''))

    def validator(key, data, errors, context):
        bypass_read_only = context.get('bypass_read_only', False)
        if bypass_read_only:
            return
        if context.get('package', False):  # package_update action
            old_value = context.get('package').extras.get('locked')
            new_value = data.get(key)
            if toolkit.asbool(new_value) != toolkit.asbool(old_value):
                raise toolkit.Invalid(_(
                    'Cannot change value of "{}" from {} to {}. This key is read-only.'
                ).format(key[-1], toolkit.asbool(old_value), toolkit.asbool(new_value)))
            elif default_value and new_value is None and old_value is None:
                data[key] = default_value
        else:  # package_create action
            if data.get(key):
                raise toolkit.Invalid(_(
                    'Cannot set value of "{}" to {}. This key is read-only.'
                ).format(key[-1], data[key]))
            elif default_value:
                data[key] = default_value

    return validator
