import ckan.plugins as p
import logging
from collections import OrderedDict
import ckan.model.license as core_licenses
import ckan.model.package as package
import ckan.plugins.toolkit as toolkit
import ckan.lib.uploader as uploader
from ckan.lib.plugins import DefaultTranslation
from ckanext.unaids.validators import (
    if_empty_guess_format,
    organization_id_exists_validator
)
from ckanext.unaids.helpers import (
    get_logo_path,
    get_all_package_downloads,
    get_autogenerated_resources,
    get_user_obj,
    get_all_organizations,
)
import ckanext.external_storage.helpers as extstorage_helpers
import ckanext.unaids.actions as actions
from ckanext.unaids import (
    auth,
    licenses
)
from ckanext.unaids.blueprints import blueprints
from ckanext.reclineview.plugin import ReclineViewBase
from ckanext.validation.interfaces import IDataValidation
from ckanext.unaids.dataset_transfer.logic import send_dataset_transfer_emails

log = logging.getLogger(__name__)


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
    p.implements(p.IPackageController, inherit=True)
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
            u'get_user_obj': get_user_obj,
            u'get_all_organizations': get_all_organizations,
            u'extstorage_resource_authz_scope': extstorage_helpers.resource_authz_scope,
            u'extstorage_resource_storage_prefix': extstorage_helpers.resource_storage_prefix,
            u'extstorage_resource_filename': extstorage_helpers.resource_filename,
            u'max_resource_size': uploader.get_max_resource_size
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

    # IPackageController
    def after_update(self, context, pkg_dict):
        if 'extras' in pkg_dict:
            org_to_allow_transfer_to = [
                item['value']
                for item in pkg_dict['extras']
                if item['key'] == 'org_to_allow_transfer_to' and item['value']
            ]
            if org_to_allow_transfer_to:
                send_dataset_transfer_emails(
                    dataset_id=pkg_dict['id'],
                    recipient_org_id=org_to_allow_transfer_to[0]
                )


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
