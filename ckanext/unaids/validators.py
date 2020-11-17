import ckan.lib.navl.dictization_functions as df
import mimetypes
import ckan.plugins.toolkit as toolkit
from ckan.common import _


def if_empty_guess_format(key, data, errors, context):
    """
    Overrides the core if_empty_guess_format validator to add the geojson
    file type to those that it guesses.
    """
    value = data[key]
    resource_id = data.get(key[:-1] + ('id',))
    # if resource_id then an update
    if (not value or value is df.Missing) and not resource_id:
        url = data.get(key[:-1] + ('url',), '')
        mimetypes.add_type('application/geo+json', '.geojson')
        mimetype, encoding = mimetypes.guess_type(url)
        if mimetype:
            data[key] = mimetype


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
