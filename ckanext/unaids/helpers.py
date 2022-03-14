# encoding: utf-8
from ckan.lib.helpers import url_for_static_or_external, check_access
from ckan.plugins.toolkit import get_action, request
from ckan.plugins import toolkit as toolkit
from ckan.common import _, g
import logging
import os
import json


log = logging.getLogger()
BULK_FILE_UPLOADER_DEFAULT_FIELDS = 'ckanext.bulk_file_uploader_default_fields'


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


def get_bulk_file_uploader_default_fields():
    return toolkit.config.get(BULK_FILE_UPLOADER_DEFAULT_FIELDS, {})


def get_current_dataset_release(dataset_id, activity_id=None):
    """Return version linked to either the most recent activity_id
        of the dataset or the one explicitly requested

    :param dataset_id: the id or name of the dataset
    :type dataset_id: string
    :param activity_id: the id of the activity
    :type activity_id: string
    :returns: version, None if no version created for the given activity.
    :rtype: dictionary
    """
    context = {'user': toolkit.g.user}
    if not activity_id:
        activities = toolkit.get_action('package_activity_list')(
            context, {'id': dataset_id}
        )
        if not activities:
            return None
        else:
            activity_id = activities[0]['id']
    releases = toolkit.get_action('dataset_version_list')(
        context, {'dataset_id': dataset_id}
    )
    for release in releases:
        if release['activity_id'] == activity_id:
            return release


def get_navigator_locale():
    return request.environ['CKAN_LANG'].split('_')[0]
