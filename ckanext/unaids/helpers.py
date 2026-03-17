# encoding: utf-8
import logging
import os
import json
import requests
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

from urllib.parse import quote, urlencode, urlparse

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

    On staging, resource URLs are CKAN download endpoints that issue a 302 redirect to a
    cross-origin Azure CDN URL. When the browser follows each redirect as a navigation,
    each new tab cancels the previous one — so only ~1 file downloads. We resolve the
    signed Azure URL server-side so the JS receives a direct CDN URL with no redirect.
    Falls back to the resource's own URL if the resource is not an LFS-backed file.
    """
    import ckan.model as model
    file_urls = []
    context = {
        'user': getattr(toolkit.g, 'user', None),
        'auth_user_obj': getattr(toolkit.g, 'userobj', None),
        'model': model,
    }
    resources = pkg_dict.get('resources', [])
    for res in resources:
        can_access_res = check_access(
            'resource_show',
            {'id': res['id'], 'resource': res}
        )
        if not can_access_res:
            continue

        url = res.get('url')
        if not url:
            continue

        # Allow-list: only http, https, and relative URLs (empty scheme).
        # Deny-lists are fragile — unknown schemes like file://, blob:, mailto: would slip through.
        if urlparse(url).scheme not in ('http', 'https', ''):
            continue

        # Try to resolve a direct signed Azure URL via blob-storage to avoid the 302 redirect
        # that causes only one file to download on staging (each navigation cancels the last).
        try:
            spec = get_action('get_resource_download_spec')(
                context, {'id': res['id'], 'resource': res}
            )
            direct_url = spec.get('href')
            if direct_url:
                url = direct_url
        except toolkit.NotAuthorized:
            pass  # user can see the resource but not download it — skip
        except Exception:
            pass  # not an LFS resource or blob-storage not installed — use original URL

        file_urls.append(url)
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


def get_profile_editor_url(**extra_query_params):
    query_params = {
        "back_url": full_current_url(),
        "after_save_url": _get_profile_editor_save_callback(),
        "lang": get_lang()
    }
    query_params.update(extra_query_params)
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
    """
    This helper is overriding build_pages_nav_main from ckanext-pages.
    Unlike the original, this version does NOT add pages to the top navbar.
    Pages are accessible via direct links, the homepage, and the footer.
    The "2026 Instructions" link is added separately in header.html template.
    """
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

    # NOTE: We intentionally do NOT add pages to the navbar here.
    # Pages clutter the top navigation and are better accessed via:
    # - The homepage help panel (Instructions buttons)
    # - The footer (About, Terms, Cookie Policy links)
    # - Direct URLs
    # The "2026 Instructions" link is added in header.html template block.

    return output


def get_localized_page_url(page_name):
    lang = toolkit.h.lang()
    if lang == 'fr':
        raw_name = f'fr-{page_name}'
    elif lang == 'pt_PT':
        raw_name = f'pt-{page_name}'
    else:
        raw_name = page_name
    name = quote(raw_name)

    return '/{}/pages/{}'.format(lang, name)


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

    # Hide the "View Error Report" link for successful or unknown validation
    link_style = ""
    if status in ['success', 'unknown']:
        link_style = 'style="display:none"'

    badge_html = '''
<a href="{validation_url}" {tags} class="validation-badge">
    <img src="{badge_url}" alt="{alt}" title="{title}"/>
    <p class="small badge-link" {link_style}>{badge_link}</p>
</a>'''.format(
        validation_url=validation_url,
        tags=tags,
        badge_url=badge_url,
        alt=messages[status],
        title=resource.get('validation_timestamp', ''),
        link_style=link_style,
        badge_link=_('View Error Report')
    )

    return badge_html


def _get_profile_editor_save_callback():
    default_locale = config.get("ckan.locale_default")
    current_lang = lang()
    site_url = config.get("ckan.site_url")
    lang_in_url = ("/" + current_lang) if current_lang and current_lang != default_locale else ""

    return f"{site_url}{lang_in_url}/profile_editor_data_receiver"


def get_administrative_boundaries():
    context = {'user': toolkit.g.user}
    try:
        group = toolkit.get_action('group_show')(
            context,
            {'id': 'geographic-health-boundaries'}
        )
    except toolkit.ObjectNotFound:
        return []
    packages_list_from_group = toolkit.get_action('group_package_show')(
        context,
        {'id': 'geographic-health-boundaries', 'limit': 4}
    )
    group['packages'] = packages_list_from_group
    return group


def dataset_lockable(dataset_id):
    try:
        dataset = toolkit.get_action("package_show")({}, {"id": dataset_id})
        dataset_type = dataset.get('type', 'dataset')
        dataset_schema = toolkit.h.scheming_get_dataset_schema(dataset_type)
        dataset_fields = []
        if dataset_schema:
            dataset_fields = dataset_schema.get('dataset_fields', [])
        dataset_field_names = [field['field_name'] for field in dataset_fields]
        return "locked" in dataset_field_names
    except toolkit.ObjectNotFound:
        return False


def build_nav_icon(menu_item, title, **kw):
    """
    Build a navigation item with icon support that doesn't double-encode HTML.

    This overrides the core CKAN build_nav_icon to fix HTML encoding issues
    where <i> tags for icons were being escaped.

    Outputs: <li><a href="..."><i class="fa fa-{icon}"></i> title</a></li>

    :param menu_item: the name of the defined menu item (e.g., 'user.read')
    :param title: text used for the link
    :param kw: additional keywords including 'icon' and url parameters

    Security: All user inputs are HTML-escaped to prevent XSS attacks.
    """
    from ckan.lib.helpers import url_for

    # Extract icon and build icon HTML if present
    icon = kw.pop('icon', None)
    icon_html = ''
    if icon:
        # Escape icon name to prevent XSS
        icon_html = '<i class="fa fa-{}"></i> '.format(html_escape(icon))

    # Check if the link is active
    controller, action = menu_item.split('.')
    item = {'action': action, 'controller': controller}
    item.update(kw)

    # Determine if link is active
    active = _link_active(item)

    # Remove highlight_controllers so they won't appear in generated urls
    item.pop('highlight_controllers', False)

    # Get the suppress_active_class if present
    suppress_active_class = kw.pop('suppress_active_class', False)

    # Build the URL (url_for is safe, returns escaped URL)
    url = url_for(menu_item, **item)

    # Build link with proper HTML handling and XSS protection
    # Escape title to prevent XSS, but keep icon_html unescaped (it's our controlled HTML)
    # Use literal() to mark HTML as safe like build_pages_nav_main does
    link = toolkit.literal(u'<a href="{}">{}{}</a>'.format(
        html_escape(url),
        icon_html,  # Already contains escaped icon name
        html_escape(title)
    ))

    # Wrap in <li> tags with active class if needed
    if active and not suppress_active_class:
        return toolkit.literal('<li class="active">') + link + toolkit.literal('</li>')
    return toolkit.literal('<li>') + link + toolkit.literal('</li>')


def _link_active(kwargs):
    """
    Check if a menu item should be marked as active based on current request.
    This is a simplified version of the core CKAN helper.
    """
    from ckan.plugins import toolkit

    try:
        controller = kwargs.get('controller')
        action = kwargs.get('action')
        highlight_controllers = kwargs.get('highlight_controllers', [])

        endpoint = toolkit.get_endpoint()
        if not endpoint:
            return False

        current_controller, current_action = endpoint

        # Check if current matches exactly
        if controller == current_controller and action == current_action:
            return True

        # Check highlight controllers
        if current_controller in highlight_controllers:
            return True

        return False
    except Exception:
        return False


def nav_link(text, *args, **kwargs):
    """
    Build a navigation link with icon support that doesn't double-encode HTML.

    This overrides the core CKAN nav_link to fix HTML encoding issues
    where <i> tags for icons were being escaped.

    :param text: text used for the link
    :param class_: CSS class(es) to add to the <a> tag
    :param icon: name of Font Awesome icon to use within the link
    :param condition: if False then no link is returned
    :param named_route: route name for the link

    Security: All user inputs are HTML-escaped to prevent XSS attacks.
    """
    from ckan.lib.helpers import url_for
    import ckan.plugins as p

    if len(args) > 1:
        raise Exception('Too many unnamed parameters supplied')

    blueprint, endpoint = p.toolkit.get_endpoint()
    if args:
        kwargs['controller'] = blueprint or None
        kwargs['action'] = endpoint or None

    named_route = kwargs.pop('named_route', '')
    condition = kwargs.pop('condition', True)

    if not condition:
        return ''

    # Extract icon and class
    icon = kwargs.pop('icon', None)
    css_class = kwargs.pop('class_', '')
    title_attr = kwargs.pop('title', kwargs.pop('title_', None))

    # Build icon HTML if present
    icon_html = ''
    if icon:
        # Escape icon name to prevent XSS
        icon_html = '<i class="fa fa-{}"></i> '.format(html_escape(icon))

    # Build the URL (url_for is safe, returns escaped URL)
    if named_route:
        url = url_for(named_route, **kwargs)
    else:
        # For non-named routes, we need to handle it differently
        url = url_for(**kwargs)

    # Build the link HTML with proper XSS protection
    # All user inputs are escaped, icon_html contains our controlled HTML with escaped icon name
    # Use literal() to mark HTML as safe like build_pages_nav_main does
    link_parts = ['<a href="', html_escape(url), '"']
    if css_class:
        link_parts.extend([' class="', html_escape(css_class), '"'])
    if title_attr:
        link_parts.extend([' title="', html_escape(title_attr), '"'])
    link_parts.extend(['>', icon_html, html_escape(str(text)), '</a>'])

    return toolkit.literal(''.join(link_parts))
