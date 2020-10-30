import ckan.logic.schema as schema_
import ckan.logic as logic
import ckan.lib.navl.dictization_functions as dfunc
import ckan.lib.dictization.model_save as model_save
import ckan.lib.dictization.model_dictize as model_dictize
from ckan.common import _
import logging

NotFound = logic.NotFound
_check_access = logic.check_access
_validate = dfunc.validate
ValidationError = logic.ValidationError


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

    user = context['user']
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
