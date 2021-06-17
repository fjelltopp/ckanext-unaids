import logging

import ckan.logic.schema as schema_
import ckan.logic as logic
import ckan.lib.navl.dictization_functions as dfunc
import ckan.lib.dictization.model_save as model_save
import ckan.lib.dictization.model_dictize as model_dictize
import ckan.plugins.toolkit as t
import ckanext.validation.helpers as validation_helpers
from ckan.common import _
from ckanext.versions.logic.dataset_version_action import get_activity_id_from_dataset_version_name, activity_dataset_show

NotFound = logic.NotFound
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
        schema = validation_helpers.validation_load_json_schema(schema_name)
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
    version_id_or_name = data_dict.get('release_id')
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
