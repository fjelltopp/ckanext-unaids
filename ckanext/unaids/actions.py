import logging
import mimetypes
import ckan.logic.schema as schema_
import ckan.logic as logic
import ckan.lib.navl.dictization_functions as dfunc
import ckan.lib.dictization.model_save as model_save
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.plugins.toolkit as t
import ckanext.unaids.custom_user_profile.logic as custom_user_profile_logic
from ckan.common import _
from ckanext.versions.logic.dataset_version_action import get_activity_id_from_dataset_version_name, activity_dataset_show
from ckanext.unaids.logic import populate_data_dictionary_from_schema
from ckanext.unaids.helpers import validation_load_json_schema

NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
_check_access = logic.check_access
_validate = dfunc.validate
ValidationError = logic.ValidationError

log = logging.getLogger(__name__)


def get_table_schema(context, data_dict):
    """
    Returns the frictionless data table schema assigned to the resource.

    :param resource_id: id of the resource
    :type resource_id: string

    :rtype: dictionary, empty if no schema specified

    Raises not found if resource doesn't exist.
    """
    resource_id = data_dict.get("resource_id")
    data_dict = {'id': resource_id}
    _check_access('resource_show', context, data_dict)
    resource = t.get_action('resource_show')(context, data_dict)
    if not resource:
        raise NotFound(_('Resource not found.'))
    schema_name = resource.get('schema')
    schema = False
    if schema_name:
        schema = validation_load_json_schema(schema_name)
    if not schema:
        schema = {}
    return schema


def task_status_update(context, data_dict):
    '''Update a task status.

    :param id: the id of the task status to update
    :type id: string
    :param entity_id:
    :type entity_id: string
    :param entity_type:
    :type entity_type: string
    :param task_type:
    :type task_type: string
    :param key:
    :type key: string
    :param value: (optional)
    :type value:
    :param state: (optional)
    :type state:
    :param last_updated: (optional)
    :type last_updated:
    :param error: (optional)
    :type error:

    :returns: the updated task status
    :rtype: dictionary

    '''
    model = context['model']
    session = model.meta.create_local_session()
    context['session'] = session

    id = data_dict.get("id")
    schema = context.get('schema') or schema_.default_task_status_schema()

    if id:
        task_status = model.TaskStatus.get(id)
        context["task_status"] = task_status

        if task_status is None:
            raise NotFound(_('TaskStatus was not found.'))

    _check_access('task_status_update', context, data_dict)

    data, errors = _validate(data_dict, schema, context)
    if errors:
        session.rollback()
        raise ValidationError(errors)

    task_status = model_save.task_status_dict_save(data, context)

    session.commit()
    session.close()
    return model_dictize.task_status_dictize(task_status, context)


@t.chained_action
@t.side_effect_free
def dataset_version_show(original_action, context, data_dict):
    version_id_or_name = data_dict.get('release')
    if version_id_or_name:
        t.check_access('package_show', context, data_dict)
        dataset_id = t.get_or_bust(data_dict, 'id')
        try:
            activity_id = get_activity_id_from_dataset_version_name(
                context,
                {
                    'dataset_id': dataset_id,
                    'version': version_id_or_name
                }
            )
        except t.ObjectNotFound:
            raise t.ObjectNotFound("Release not found for this dataset")
        dataset = activity_dataset_show(
            context,
            {
                'activity_id': activity_id,
                'dataset_id': dataset_id
            }
        )
        for resource in dataset['resources']:
            if resource['url_type'] == 'upload':
                resource['url'] = "{}?activity_id={}".format(resource['url'], activity_id)
        return dataset
    else:
        return original_action(context, data_dict)


@t.chained_action
@t.side_effect_free
def package_activity_list(original_action, context, data_dict):
    activity_list = original_action(context, data_dict)
    dataset_id = data_dict['id']
    releases_list = t.get_action('dataset_version_list')(
        context,
        {
            'dataset_id': dataset_id,
        }
    )
    activity_to_release_name = {r['activity_id']: r['name'] for r in releases_list}
    for activity in activity_list:
        activity['release_name'] = activity_to_release_name.get(activity['id'])
    return activity_list


@logic.side_effect_free
def format_guess(context, data_dict):
    """
    Uses mimetypes to guess the file format for a given filename. This action
    should provide the one true source of file format guessing logic.  It
    should be used by both the server-side validation logic and the client-side
    Javascript logic.  Note that the unified_resource_format depends on the
    ckan.resource_formats config file - which has been overriden by this
    extension in order to include addtional file formats.

    :param filename: The name of the file
    :rtype: dictionary with `mimetype` and `format` keys. Values are `None` if
        no format can be guessed.
    """
    filename = data_dict.get('filename', "")
    mimetypes.add_type('application/geo+json', '.geojson')
    mimetypes.add_type('application/pjnz', '.pjnz')
    mimetype, encoding = mimetypes.guess_type(filename)
    if mimetype:
        format = t.h.get('unified_resource_format')(mimetype)
        return {'mimetype': mimetype, 'format': format}
    else:
        return {'mimetype': None, 'format': None}


@logic.side_effect_free
def user_show_me(context, resource_dict):
    """
    Returns the current user object.  Raises NotAuthorized error if no user
    object found.

    No input params.

    :rtype dictionary
    :returns The user object as a dictionary, which takes the following structure:
        ```
            {
                "id": "7f88caf3-e68b-4c96-883e-b49f3d547d84",
                "name": "fjelltopp_editor",
                "fullname": "Fjelltopp Editor",
                "email": "fjelltopp_editor@fjelltopp.org",
                "created": "2021-10-29 12:51:56.277305",
                "reset_key": null,
                "about": null,
                "activity_streams_email_notifications": false,
                "sysadmin": false,
                "state": "active",
                "image_url": null,
                "plugin_extras": null
            }
        ```

    """
    auth_user_obj = context.get('auth_user_obj')
    if auth_user_obj:
        return auth_user_obj.as_dict()
    else:
        raise NotAuthorized


def populate_data_dictionary(context, data_dict):
    resource_id = logic.get_or_bust(data_dict, 'resource_id')
    resource_dict = t.get_action('resource_show')(
        context,
        {'id': resource_id}
    )
    populate_data_dictionary_from_schema(context, resource_dict)


@logic.side_effect_free
@t.chained_action
def user_show(original_action, context, data_dict):
    user = original_action(context, data_dict)
    user_obj = custom_user_profile_logic.get_user_obj(context)

    extras = custom_user_profile_logic.init_plugin_extras(user_obj.plugin_extras)
    extras = custom_user_profile_logic.format_plugin_extras(extras["unaids"])

    user.update(extras)
    return user


@logic.side_effect_free
@t.chained_action
def user_list(original_action, context, data_dict):
    users = original_action(context, data_dict)
    for user in users:
        if type(user) is dict:
            user_obj = custom_user_profile_logic.get_user_obj({
                'model': context['model'],
                'user': user['name']
            })
            extras = custom_user_profile_logic.init_plugin_extras(user_obj.plugin_extras)
            extras = custom_user_profile_logic.format_plugin_extras(extras["unaids"])
            user.update(extras)
    return users


@t.chained_action
def package_create(next_action, context, data_dict):
    dataset_type = data_dict.get('type', '')
    valid_types = t.get_action("scheming_dataset_schema_list")(context, {})
    valid_types = set(valid_types) | {'dataset', 'harvest'}
    if dataset_type:
        if dataset_type not in valid_types:
            raise t.ValidationError(
                f"Type '{dataset_type}' is invalid, valid types are: '"
                f"{', '.join(valid_types)}'"
            )
    return next_action(context, data_dict)


def time_ago_from_timestamp(context, data_dict):
    return t.h.time_ago_from_timestamp(data_dict.get('timestamp'))


def _get_named_version(dataset_id, name):
    locked_name = t.config.get("ckanext.unaids.locked_release_name", "Locked")
    versions = t.get_action("dataset_version_list")({}, {"dataset_id": dataset_id})
    for version in versions:
        if version['name'] == locked_name:
            return version
    return {}


def dataset_lock(context, data_dict):
    _check_access('dataset_lock', context, data_dict)
    dataset_id = t.get_or_bust(data_dict, "id")
    if not t.h.dataset_lockable(dataset_id):
        raise t.ValidationError(t._("Datasets of this type cannot be locked."))
    locked_name = t.config.get("ckanext.unaids.locked_release_name", "Locked")
    if _get_named_version(dataset_id, locked_name):
        raise t.ValidationError(t._(
            "Can't lock dataset because a release named '{}' already "
            "exists. Please rename or delete this release first. ".format(locked_name)
        ))
    context['bypass_read_only'] = True
    t.get_action("package_patch")(
        context,
        {"id": dataset_id, "locked": True}
    )
    t.get_action("dataset_version_create")(context, {
        "dataset_id": dataset_id,
        "name": locked_name,
        "notes": t._("This dataset has been made read-only by a system administrator")
    })


def dataset_unlock(context, data_dict):
    _check_access('dataset_lock', context, data_dict)
    dataset_id = t.get_or_bust(data_dict, "id")
    if not t.h.dataset_lockable(dataset_id):
        raise t.ValidationError(t._("Datasets of this type cannot be locked / unlocked."))
    context['bypass_read_only'] = True
    context['ignore_auth'] = True
    t.get_action("package_patch")(
        context,
        {"id": dataset_id, "locked": False}
    )
    try:
        locked_name = t.config.get("ckanext.unaids.locked_release_name", "Locked")
        locked_version = _get_named_version(dataset_id, locked_name)
        t.get_action("version_delete")(context, {"version_id": locked_version['id']})
    except Exception:
        log.exception(f"Failed to delete version '{locked_name}'' "
                      f"whilst unlocking dataset {dataset_id}")
        raise t.ObjectNotFound(t._(
            "Dataset is unlocked, but the associated release could not be deleted. "
            "Please manually review the releases list and cleanup if necessary."
        ))
