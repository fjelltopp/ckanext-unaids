import logging
from flask import Blueprint

from ckan.plugins import toolkit

log = logging.getLogger(__name__)

dataset_lock = Blueprint(
    'dataset_lock',
    __name__,
    url_prefix="/dataset"
)


@dataset_lock.route('/<dataset_id>/lock', methods=['POST'])
def lock(dataset_id):
    try:
        toolkit.get_action('dataset_lock')({}, {'id': dataset_id})
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, toolkit._(f'Dataset {dataset_id} not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(
            403,
            toolkit._(f'Unauthorized to lock package {dataset_id}')
        )
    toolkit.h.flash_success(toolkit._("Successfully locked this dataset. This dataset is now read only."))
    return toolkit.h.redirect_to(toolkit.url_for('dataset.read', id=dataset_id))


@dataset_lock.route('/<dataset_id>/unlock', methods=['POST'])
def unlock(dataset_id):
    try:
        toolkit.get_action('dataset_unlock')({}, {'id': dataset_id})
    except toolkit.ObjectNotFound:
        return toolkit.abort(404, toolkit._(f'Dataset {dataset_id} not found'))
    except toolkit.NotAuthorized:
        return toolkit.abort(
            403,
            toolkit._(f'Unauthorized to lock package {dataset_id}')
        )
    toolkit.h.flash_success(toolkit._("Successfully unlocked this dataset. This dataset can now be edited."))
    return toolkit.h.redirect_to(toolkit.url_for('dataset.read', id=dataset_id))
