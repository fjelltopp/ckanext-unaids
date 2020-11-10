# encoding: utf-8
import logging
import cStringIO
import json
import os
from flask import Blueprint, Response
from ckan import model
from ckan.plugins import toolkit
import ckan.lib.helpers as h
from ckanext.validation.jobs import _load_dataframe

unaids_dataset_transfer = Blueprint(
    u'unaids_dataset_transfer',
    __name__,
    url_prefix=u'/validation'
)


def process_dataset_transfer(dataset_id):
    toolkit.check_access('package_update', {'id': dataset_id})
    dataset = toolkit.get_action('package_show')({}, {'id': dataset_id})
    dataset.update({
        'owner_org': dataset['org_to_allow_transfer_to'],
        'org_to_allow_transfer_to': ''
    })
    toolkit.get_action('package_update')({
        'model': model,
        'session': model.Session,
        'user': toolkit.g.user
    }, dataset)
    return h.redirect_to(controller='dataset', action='read', id=dataset_id)


unaids_dataset_transfer.add_url_rule(
    u'/transfer_dataset/<dataset_id>',
    view_func=process_dataset_transfer
)
