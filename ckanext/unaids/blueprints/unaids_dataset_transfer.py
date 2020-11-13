# encoding: utf-8
from flask import Blueprint
from ckan import model
from ckan.plugins import toolkit
from ckan.common import _, c
import ckan.lib.helpers as h
import ckanext.unaids.helpers as helpers
import ckan.logic as logic
import ckan.lib.base as base

unaids_dataset_transfer = Blueprint(
    u'unaids_dataset_transfer',
    __name__,
    url_prefix=u'/validation'
)


def process_dataset_transfer(dataset_id):
    dataset = toolkit.get_action('package_show')({}, {'id': dataset_id})
    
    # validate user can transfer dataset
    valid = helpers.check_organization_update_access(
        dataset['org_to_allow_transfer_to']
    )
    if not valid:
        return base.abort(403, _(u'You cannot carry out this action'))

    # update dataset
    dataset.update({
        'owner_org': dataset['org_to_allow_transfer_to'],
        'org_to_allow_transfer_to': ''
    })
    toolkit.get_action('package_update')({
        'model': model,
        'session': model.Session,
        'ignore_auth': True
    }, dataset)

    # return success
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
