# encoding: utf-8
from ckan.lib.helpers import url_for_static_or_external, check_access
from ckan.plugins.toolkit import get_action
import ckan.plugins.toolkit as toolkit
import ckan.lib.uploader as uploader
from ckan.common import _, g
from six.moves.urllib.parse import urlparse
from typing import Optional
import logging
import os
from os import path
import json


log = logging.getLogger()
STORAGE_NAMESPACE_CONF_KEY = 'ckanext.external_storage.storage_namespace'


def get_all_package_downloads(pkg_dict):
    """
    Get all the urls of resources the user has access to in the package.
    """
    file_urls = []
    for res in pkg_dict['resources']:
        can_access_res = check_access(
            'resource_show',
            {'id': res['id'], 'resource': res}
        )
        if can_access_res and res.get('url'):
            file_urls.append(res.get('url'))

    for res in get_autogenerated_resources(pkg_dict):
        file_urls.append(res['link'])

    return json.dumps(file_urls)


def get_logo_path(logo_filename, language):
    """
    Returns the URL for static content that requires localization.
    """
    log.debug("Called get_logo_path")
    log.debug("Logo filename: {}".format(logo_filename))
    log.debug("Language: {}".format(language))

    current_directory = os.path.dirname(
        os.path.abspath(__file__)
    )
    public_directory = current_directory + "/theme/public"
    localised_logo_filename = "/{}_{}".format(language, logo_filename[1:])
    localised_logo_path = public_directory + localised_logo_filename

    log.debug("Localised logo path: {}".format(localised_logo_path))

    if os.path.exists(localised_logo_path):
        return url_for_static_or_external(localised_logo_filename)
    else:
        return url_for_static_or_external(logo_filename)


def get_autogenerated_resources(pkg):
    """
    Identify which pre-specified resources are defined in the package
    schema but currently missing from the actual package. Return the
    details of those missing resources. A pre-specified resource is
    defined in the package schema e.g a HIVE package should contain ART
    data, ANC data and SVY data.
    """

    autogenerated_resources = []

    if pkg['type'] == 'geographic-data-package':

        uploaded_resources = [x['resource_type'] for x in pkg.get('resources')]
        required_resources = [
            'geographic-location-hierarchy',
            'geographic-regional-geometry'
        ]

        if set(required_resources) <= set(uploaded_resources):
            autogenerated_resources.append({
                'name': _('Naomi Geographic Data Input'),
                'about': _('Geographic data formatted for the Naomi model.'),
                'link': '/validation/geodata/' + pkg['id'],
                'format': 'geojson'
            })

    return autogenerated_resources


def get_user_obj(field=""):
    """
    Returns an attribute of the user object, or returns the whole user object.
    """
    return getattr(g.userobj, field, g.userobj)


def get_all_organizations():
    data_dict = {'all_fields': True}
    results = get_action('organization_list')({}, data_dict)
    return results


def storage_namespace():
    """Get the storage namespace for this CKAN instance
    """
    ns = toolkit.config.get(STORAGE_NAMESPACE_CONF_KEY)
    if ns:
        return ns
    return 'ckan'


def get_extstorage_resource_storage_prefix(package_name, org_name=None):
    # type: (str, Optional[str]) -> str
    """Get the resource storage prefix for a package name
    """
    if org_name is None:
        org_name = storage_namespace()
    return '{}/{}'.format(org_name, package_name)


def get_extstorage_resource_authz_scope(package_name, actions=None, org_name=None, resource_id=None):
    # type: (str, Optional[str], Optional[str], Optional[str]) -> str
    """Get the authorization scope for package resources
    """
    if actions is None:
        actions = 'read,write'
    if resource_id is None:
        resource_id = '*'
    return 'obj:{}/{}:{}'.format(get_extstorage_resource_storage_prefix(package_name, org_name), resource_id, actions)


def get_extstorage_resource_filename(resource):
    """Get original file name from resource
    """
    if 'url' not in resource:
        return resource['name']

    if resource['url'][0:6] in {'http:/', 'https:'}:
        url_path = urlparse(resource['url']).path
        return path.basename(url_path)
    return resource['url']


def get_max_resource_size():
    """Get the max resource size for this CKAN instance
    """
    return uploader.get_max_resource_size()
