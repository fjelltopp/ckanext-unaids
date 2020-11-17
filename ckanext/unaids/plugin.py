import ckan.plugins as p
import logging
import licenses
import mimetypes
import ckan.model.license as core_licenses
import ckan.model.package as package
from blueprints import blueprints
from collections import OrderedDict
from ckan.lib.plugins import DefaultTranslation
import ckan.lib.navl.dictization_functions as df
from ckanext.unaids.helpers import (
    get_logo_path,
    get_all_package_downloads,
    get_autogenerated_resources,
    get_user_obj
)
import ckanext.unaids.actions as actions
from ckanext.unaids import auth
import ckan.plugins.toolkit as toolkit
from ckanext.reclineview.plugin import ReclineViewBase
from ckanext.validation.interfaces import IDataValidation
from ckan.common import _

log = logging.getLogger(__name__)


def if_empty_guess_format(key, data, errors, context):
    """
    Overrides the core if_empty_guess_format validator to add the geojson
    file type to those that it guesses.
    """
    value = data[key]
    resource_id = data.get(key[:-1] + ('id',))
    # if resource_id then an update
    if (not value or value is df.Missing) and not resource_id:
        url = data.get(key[:-1] + ('url',), '')
        mimetypes.add_type('application/geo+json', '.geojson')
        mimetype, encoding = mimetypes.guess_type(url)
        if mimetype:
            data[key] = mimetype


def organization_id_exists_validator(key, data, errors, context):
    """
    Make sure an field is a valid organization_id
    """
    value = data.get(key)
    if value:
        all_organizaions = toolkit.get_action('organization_list')(
            {}, {'all_fields': True}
        )
        is_valid = value in [
            x['id']
            for x in all_organizaions
        ]
        if not is_valid:
            raise df.Invalid(_('Invalid organization'))


def add_licenses():
    package.Package._license_register = core_licenses.LicenseRegister()
    package.Package._license_register.licenses = [
        core_licenses.License(
            licenses.LicenseCreativeCommonsIntergovernmentalOrgs()),
        core_licenses.License(
            core_licenses.LicenseNotSpecified())
        ]


class UNAIDSPlugin(p.SingletonPlugin, DefaultTranslation):
    """
    This plugin implements the configurations needed for AIDS data exchange

    """

    p.implements(p.IConfigurer)
    p.implements(p.IFacets, inherit=True)
    p.implements(p.IBlueprint)
    p.implements(p.ITranslation)
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IAuthFunctions)
    p.implements(p.IValidators)
    p.implements(p.IActions)
    p.implements(IDataValidation)

    # IConfigurer
    def update_config(self, config):
        '''
        This method allows to access and modify the CKAN configuration object
        '''
        add_licenses()
        log.info("UNAIDS Plugin is enabled")
        p.toolkit.add_template_directory(config, 'theme/templates')
        p.toolkit.add_public_directory(config, 'theme/public')
        toolkit.add_resource('assets', 'ckanext-unaids')

    def get_blueprint(self):
        return blueprints

    def get_actions(self):
        return {
            u'task_status_update': actions.task_status_update,
            u'get_table_schema': actions.get_table_schema
        }

    def dataset_facets(self, facet_dict, package_type):
        new_fd = OrderedDict()
        new_fd['organization'] = p.toolkit._('Organization')
        new_fd['type_name'] = p.toolkit._('Data Type')
        new_fd['tags'] = p.toolkit._('Tags')
        new_fd["year"] = p.toolkit._('Year')
        new_fd["geo-location"] = p.toolkit._('Location')
        return new_fd

    def organization_facets(self, facet_dict, org_type, package_type):

        return facet_dict

    # ITemplateHelpers
    def get_helpers(self):
        return {
            u'get_logo_path': get_logo_path,
            u'get_all_package_downloads': get_all_package_downloads,
            u'get_autogenerated_resources': get_autogenerated_resources,
            u'get_user_obj': get_user_obj
        }

    # IAuthFunctions
    def get_auth_functions(self):
        return {
            'unaids_organization_update': auth.unaids_organization_update
        }

    def get_validators(self):
        return{
            'if_empty_guess_format': if_empty_guess_format,
            'organization_id_exists': organization_id_exists_validator
        }

    def can_validate(self, context, data_dict):
        if data_dict.get('validate_package'):
            logging.warning("VALIDATING ENTIRE PACKAGE")
            toolkit.get_action('resource_validation_run_batch')(
                context,
                {'dataset_ids': data_dict['package_id']}
            )
        if data_dict.get('schema'):
            return True


class UNAIDSReclineView(ReclineViewBase):
    '''
    This override of the recline view plugin allows data explorers to be auto
    created for geojson files.
    '''

    def info(self):
        return {'name': 'unaids_recline_view',
                'title': 'Data Explorer',
                'filterable': True,
                'icon': 'table',
                'requires_datastore': False,
                'default_title': p.toolkit._('Data Explorer'),
                }

    def can_view(self, data_dict):
        resource = data_dict['resource']

        if (resource.get('datastore_active') or
                '_datastore_only_resource' in resource.get('url', '')):
            return True
        resource_format = resource.get('format', None)

        if resource_format:
            return resource_format.lower() in [
                'csv', 'xls', 'xlsx', 'tsv', 'geojson'
            ]
        else:
            return False
