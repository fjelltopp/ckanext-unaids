# encoding: utf-8
from flask import Blueprint
from ckan import model
from ckan.plugins import toolkit
from ckan.common import _
import ckan.lib.helpers as h
import ckan.logic as logic
import ckan.lib.base as base
import json


unaids_dataset_transfer = Blueprint(
    u'unaids_dataset_transfer',
    __name__,
    url_prefix=u'/validation'
)


@unaids_dataset_transfer.app_template_filter()
def json_dumps(json_obj):
    if not json_obj:
        return '{}'
    return json.dumps(json_obj)


def process_dataset_transfer(dataset_id):
    dataset = toolkit.get_action('package_show')({}, {'id': dataset_id})

    try:
        toolkit.check_access(
            'unaids_organization_update',
            {'user': toolkit.g.user},
            {'id': dataset['org_to_allow_transfer_to']}
        )
    except logic.NotAuthorized:
        return base.abort(403, _('You cannot carry out this action'))

    dataset.update({
        'owner_org': dataset['org_to_allow_transfer_to'],
        'org_to_allow_transfer_to': None
    })
    toolkit.get_action('package_update')({
        'user': '',
        'model': model,
        'session': model.Session,
        'ignore_auth': True
    }, dataset)

    h.flash_success(
        ' '.join([
            _('Dataset moved to'),
            h.get_organization(dataset['owner_org'])['display_name']
        ])
    )
    return h.redirect_to(
        controller='dataset', action='read', id=dataset_id
    )


unaids_dataset_transfer.add_url_rule(
    u'/transfer_dataset/<dataset_id>',
    view_func=process_dataset_transfer
)
