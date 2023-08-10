# encoding: utf-8
import logging
import os
import json
import requests
import six
from ckan.lib.helpers import url_for_static_or_external, check_access, full_current_url, lang
from ckan.lib.i18n import get_lang
from ckan.plugins.toolkit import get_action, request
from ckan.plugins import toolkit
from ckan.common import _, g, asbool, config
from ckan.lib.helpers import build_nav_main as core_build_nav_main


try:
    from html import escape as html_escape
except ImportError:
    from cgi import escape as html_escape

from urllib.parse import quote, urlencode

log = logging.getLogger()
BULK_FILE_UPLOADER_DEFAULT_FIELDS = 'ckanext.bulk_file_uploader_default_fields'

log = logging.getLogger(__name__)


def _files_from_directory(path, extension=".json"):
    listed_files = {}
    for root, dirs, files in os.walk(path):
        for file in files:
            if extension in file:
                name = file.split(".json")[0]
                listed_files[name] = os.path.join(root, file)
    return listed_files


def get_schema_filepath(schema):
    schema_directory = toolkit.config["ckanext.unaids.schema_directory"]
    schemas = _files_from_directory(schema_directory)
    return schemas.get(schema)


def validation_load_json_schema(schema):
    try:
        # When updating a resource there's already an existing JSON schema
        # attached to the resource
        if isinstance(schema, dict):
            return schema

        if schema.startswith("http"):
            r = requests.get(schema)
            return r.json()

        schema_filepath = get_schema_filepath(schema)
        if schema_filepath:
            with open(schema_filepath, "rb") as schema_file:
                return json.load(schema_file)

        return json.loads(schema)

    except json.JSONDecodeError as e:
        log.error("Error loading schema: " + schema)
        log.exception(e)
        return None


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


def get_profile_editor_url():
    query_params = {
        "back_url": full_current_url(),
        "after_save_url": _get_profile_editor_save_callback(),
        "lang": get_lang()
    }
    domain_part = config.get("ckanext.unaids.profile_editor_url", "")
    encoded_query_params = urlencode(query_params)

    return f"{domain_part}?{encoded_query_params}"


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


def get_language_code():
    return request.environ['CKAN_LANG'].split('_')[0]


def build_pages_nav_main(*args):
    about_menu = toolkit.asbool(toolkit.config.get('ckanext.pages.about_menu', True))
    group_menu = toolkit.asbool(toolkit.config.get('ckanext.pages.group_menu', True))
    org_menu = toolkit.asbool(toolkit.config.get('ckanext.pages.organization_menu', True))

    # Different CKAN versions use different route names - gotta catch em all!
    about_menu_routes = ['about', 'home.about']
    group_menu_routes = ['group_index', 'home.group_index', 'group.index']
    org_menu_routes = ['organizations_index', 'home.organizations_index', 'organization.index']

    new_args = []
    for arg in args:
        if arg[0] in about_menu_routes and not about_menu:
            continue
        if arg[0] in org_menu_routes and not org_menu:
            continue
        if arg[0] in group_menu_routes and not group_menu:
            continue
        new_args.append(arg)

    output = core_build_nav_main(*new_args)

    # do not display any private pages in menu even for sysadmins
    pages_list = toolkit.get_action('ckanext_pages_list')(None, {'order': True, 'private': False})

    page_name = ''
    if toolkit.check_ckan_version(u'2.9'):
        is_current_page = toolkit.get_endpoint() in (('pages', 'show'), ('pages', 'blog_show'))
    else:
        is_current_page = (
                hasattr(toolkit.c, 'action') and toolkit.c.action in ('pages_show', 'blog_show')
                and toolkit.c.controller == 'ckanext.pages.controller:PagesController')
    if is_current_page:
        page_name = toolkit.request.path.split('/')[-1]

    for page in pages_list:
        type_ = 'blog' if page['page_type'] == 'blog' else 'pages'
        if six.PY2:
            name = quote(page['name'].encode('utf-8')).decode('utf-8')
        else:
            name = quote(page['name'])
        title = html_escape(_(page['title']))
        link = toolkit.h.literal(u'<a href="/{}/{}/{}">{}</a>'.format(toolkit.h.lang(), type_, name, title))
        if page['name'] == page_name:
            li = toolkit.literal('<li class="active">') + link + toolkit.literal('</li>')
        else:
            li = toolkit.literal('<li>') + link + toolkit.literal('</li>')
        output = output + li

    return output


def get_google_analytics_id():
    from_env = os.environ.get('CKAN_GOOGLE_ANALYTICS_ID', None)
    if not from_env:
        return toolkit.config.get('ckan.google_analytics_id', None)
    return from_env


def is_an_estimates_dataset(dataset_type_name):
    return 'estimates' in dataset_type_name.lower()


def url_encode(url):
    return quote(url, safe='/:?=&')


def unaids_get_validation_badge(resource, in_listing=False):

    if in_listing and not asbool(
            toolkit.config.get('ckanext.validation.show_badges_in_listings', True)):
        return ''

    if not resource.get('validation_status'):
        return ''

    messages = {
        'success': _('Valid data'),
        'failure': _('Invalid data'),
        'error': _('Error during validation'),
        'unknown': _('Data validation unknown'),
    }

    if resource['validation_status'] in ['success', 'failure', 'error']:
        status = resource['validation_status']
    else:
        status = 'unknown'

    validation_url = toolkit.url_for(
        'validation_read',
        id=resource['package_id'],
        resource_id=resource['id']
    )

    tags = ""
    if status == 'unknown':
        tags += "data-module='validation-badge' data-module-resource='{}'".format(
            resource['id']
        )

    badge_url = url_for_static_or_external(
        '/images/badges/{}-{}.gif'.format(toolkit.h.lang(), status))

    link_visibility = ""
    if status in ['success', 'unknown']:
        link_visibility = 'hidden'

    badge_html = '''
<a href="{validation_url}" {tags} class="validation-badge">
    <img src="{badge_url}" alt="{alt}" title="{title}"/>
    <p class="small badge-link {link_visibility}">{badge_link}</p>
</a>'''.format(
        validation_url=validation_url,
        tags=tags,
        badge_url=badge_url,
        alt=messages[status],
        title=resource.get('validation_timestamp', ''),
        link_visibility=link_visibility,
        badge_link=_('View Error Report')
    )

    return badge_html


def _get_profile_editor_save_callback():
    default_locale = config.get("ckan.locale_default")
    current_lang = lang()
    site_url = config.get("ckan.site_url")
    lang_in_url = ("/" + current_lang) if current_lang and current_lang != default_locale else ""

    return f"{site_url}{lang_in_url}/profile_editor_data_receiver"
