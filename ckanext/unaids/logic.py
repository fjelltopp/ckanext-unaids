from ckan import model
from ckan.lib.munge import substitute_ascii_equivalents
from ckan.plugins import toolkit
from ckanext.unaids.helpers import validation_load_json_schema


def validate_resource_upload_fields(context, resource_dict):
    # sha256 and lfs_prefix are the giftless blob-storage upload fields. `size`
    # is a standard CKAN field present on any stored resource, so it must NOT
    # gate the "is this a blob-storage upload" check. Otherwise re-saves that
    # carry `size` but not the giftless fields (e.g. ckanext-validation patching
    # validation_status) wrongly fail with "Invalid blob storage upload fields",
    # which silently blocks validation on the resource-create path.
    upload_has_sha256 = bool(resource_dict.get("sha256"))
    upload_has_lfs_prefix = bool(resource_dict.get("lfs_prefix"))

    if upload_has_sha256 != upload_has_lfs_prefix:
        raise toolkit.ValidationError(
            ["Invalid blob storage upload fields. sha256 and lfs_prefix needs to be provided."])
    elif not upload_has_sha256:
        return None
    else:
        sha256 = resource_dict.get("sha256")
        lfs_prefix = resource_dict.get("lfs_prefix")
        try:
            toolkit.get_validator('valid_sha256')(sha256)
            toolkit.get_validator('valid_lfs_prefix')(lfs_prefix)
        except toolkit.Invalid as err:
            raise toolkit.ValidationError([err.error])


def update_filename_in_resource_url(resource):
    if resource['url_type'] == 'upload':
        filename = model.Resource.get(resource['id']).url
        # core CKAN functionality fails for non ascii filenames
        filename = substitute_ascii_equivalents(filename)
        url_segments = resource['url'].split('/')
        if filename and len(url_segments):
            new_url_segments = url_segments[:-1] + [filename]
            resource['url'] = u'/'.join(new_url_segments)
    return resource


def populate_data_dictionary_from_schema(context, resource_dict):
    table_schema_name = toolkit.get_or_bust(resource_dict, 'schema')
    table_schema = validation_load_json_schema(table_schema_name)

    if not table_schema:
        raise toolkit.ObjectNotFound(
            'Resource table schema "{}" does not exist'.format(table_schema)
        )

    field_schemas = {field['name']: field for field in table_schema.get('fields')}

    try:
        fields = toolkit.get_action(u'datastore_search')(
            context, {u'resource_id': resource_dict['id']}
        )[u'fields']

    except toolkit.ObjectNotFound:
        raise toolkit.ObjectNotFound(
            'Resource "{}" must first be uploaded to the datastore in order to '
            'update the data dictionary.'.format(resource_dict['id'])
        )

    fields = fields[1:]  # Hack: to get rid of _id field.

    for field in fields:
        field_id = field[u'id']

        if field_id in field_schemas:

            field[u'info'] = {
                u'label': field_schemas[field_id].get(u'title', field_id),
                u'notes': field_schemas[field_id].get(u'description', field_id)
            }

    toolkit.get_action(u'datastore_create')(
        context, {
            u'resource_id': resource_dict[u'id'],
            u'force': True,
            u'fields': fields
        }
    )
