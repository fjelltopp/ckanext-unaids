import datetime
import logging
from collections import OrderedDict

from giftless_client import LfsClient
from werkzeug.datastructures import FileStorage as FlaskFileStorage
from ckanext.saml2auth.interfaces import ISaml2Auth

import ckan.plugins as p
import ckan.model.license as core_licenses
import ckan.model.package as package
import ckan.plugins.toolkit as toolkit
import ckan.lib.uploader as uploader
from ckan.lib.plugins import DefaultTranslation
from ckan.logic import get_action
from ckan.views import _identify_user_default
from ckanext.blob_storage.interfaces import IResourceDownloadHandler
from ckanext.unaids.dataset_transfer.model import tables_exists
from ckanext.unaids import custom_user_profile
from ckanext.unaids.validators import (
    if_empty_guess_format,
    organization_id_exists_validator,
)
from ckanext.unaids.helpers import (
    get_logo_path,
    get_all_package_downloads,
    get_user_obj,
    get_all_organizations,
    get_bulk_file_uploader_default_fields,
    get_current_dataset_release,
    get_language_code,
    build_pages_nav_main,
    get_google_analytics_id,
    is_an_estimates_dataset,
    url_encode
)
import ckanext.blob_storage.helpers as blobstorage_helpers
import ckanext.unaids.actions as actions
import ckanext.unaids.auth_logic as auth_logic
from ckanext.unaids import auth, licenses, command, logic
from ckanext.unaids.blueprints import blueprints
from ckanext.reclineview.plugin import ReclineViewBase
from ckanext.validation.interfaces import IDataValidation
from ckanext.unaids.dataset_transfer.logic import send_dataset_transfer_emails
from ckanext.datapusher.interfaces import IDataPusher

log = logging.getLogger(__name__)


def add_licenses():
    package.Package._license_register = core_licenses.LicenseRegister()
    package.Package._license_register.licenses = [
        core_licenses.License(licenses.LicenseCreativeCommonsIntergovernmentalOrgs()),
        core_licenses.License(core_licenses.LicenseNotSpecified()),
    ]


def initialize_g_userobj_using_private_core_ckan_method():
    _identify_user_default()


class UNAIDSPlugin(p.SingletonPlugin, DefaultTranslation):
    """
    This plugin implements the configurations needed for AIDS data exchange

    """

    p.implements(p.IClick)
    p.implements(p.IConfigurer)
    p.implements(p.IFacets, inherit=True)
    p.implements(p.IBlueprint)
    p.implements(p.ITranslation)
    p.implements(p.IConfigurer)
    p.implements(p.ITemplateHelpers)
    p.implements(p.IAuthFunctions)
    p.implements(ISaml2Auth, inherit=True)
    p.implements(p.IPackageController, inherit=True)
    p.implements(p.IResourceController, inherit=True)
    p.implements(p.IValidators)
    p.implements(p.IActions)
    p.implements(IDataValidation)
    p.implements(IResourceDownloadHandler, inherit=True)
    p.implements(IDataPusher, inherit=True)
    p.implements(p.IAuthenticator, inherit=True)
    p.implements(p.IMiddleware, inherit=True)

    # IClick
    def get_commands(self):
        return command.get_commands()

    # IConfigurer
    def update_config(self, config):
        if not tables_exists():
            log.critical(
                "The unaids extension requires a database setup. Please run "
                "the following to create the database tables: \n"
                "ckan unaids initdb"
            )
        else:
            log.debug("UNAIDS tables verified to exist")
        add_licenses()
        log.info("UNAIDS Plugin is enabled")
        p.toolkit.add_template_directory(config, "theme/templates")
        p.toolkit.add_public_directory(config, "theme/public")
        toolkit.add_resource("assets", "ckanext-unaids")

    def get_blueprint(self):
        return blueprints

    def get_actions(self):
        return {
            "task_status_update": actions.task_status_update,
            "get_table_schema": actions.get_table_schema,
            "package_show": actions.dataset_version_show,
            "package_activity_list": actions.package_activity_list,
            "format_guess": actions.format_guess,
            "user_show_me": actions.user_show_me,
            "populate_data_dictionary": actions.populate_data_dictionary,
            "user_show": actions.user_show,
            "time_ago_from_timestamp": actions.time_ago_from_timestamp,
        }

    def dataset_facets(self, facet_dict, package_type):
        new_fd = OrderedDict()
        new_fd["organization"] = p.toolkit._("Organization")
        new_fd["type_name"] = p.toolkit._("Data Type")
        new_fd["tags"] = p.toolkit._("Tags")
        new_fd["year"] = p.toolkit._("Year")
        new_fd["geo-location"] = p.toolkit._("Location")
        return new_fd

    def organization_facets(self, facet_dict, org_type, package_type):

        return facet_dict

    # ITemplateHelpers
    def get_helpers(self):
        return {
            "get_logo_path": get_logo_path,
            "get_all_package_downloads": get_all_package_downloads,
            "get_user_obj": get_user_obj,
            "get_all_organizations": get_all_organizations,
            "blob_storage_resource_filename": blobstorage_helpers.resource_filename,
            "max_resource_size": uploader.get_max_resource_size,
            "bulk_file_uploader_default_fields": get_bulk_file_uploader_default_fields,
            "get_current_dataset_release": get_current_dataset_release,
            "get_language_code": get_language_code,
            "build_nav_main": build_pages_nav_main,
            "get_google_analytics_id": get_google_analytics_id,
            "is_an_estimates_dataset": is_an_estimates_dataset,
            "url_encode": url_encode
        }

    # IAuthFunctions
    def get_auth_functions(self):
        return {"unaids_organization_update": auth.unaids_organization_update}

    def get_validators(self):
        return {
            "if_empty_guess_format": if_empty_guess_format,
            "organization_id_exists": organization_id_exists_validator,
        }

    def can_validate(self, context, data_dict):
        if data_dict.get("validate_package"):
            logging.warning("VALIDATING ENTIRE PACKAGE")
            toolkit.get_action("resource_validation_run_batch")(
                context, {"dataset_ids": data_dict["package_id"]}
            )
        if data_dict.get("schema"):
            return True

    # IPackageController
    def after_update(self, context, pkg_dict):
        if "extras" in pkg_dict:
            org_to_allow_transfer_to = [
                item["value"]
                for item in pkg_dict["extras"]
                if item["key"] == "org_to_allow_transfer_to" and item["value"]
            ]
            if org_to_allow_transfer_to:
                send_dataset_transfer_emails(
                    dataset_id=pkg_dict["id"],
                    recipient_org_id=org_to_allow_transfer_to[0],
                )

    # IResourceController
    def _process_schema_fields(self, data_dict):
        """
        Here we overload the default schema processing (from frictionlessdata/ckanext-validation)
        to allow for the fact that we just pass a schema name around rather than the schema url
        or a schema JSON.
        """

        schema = data_dict.pop("schema", None)
        if schema:
            schema_json = logic.validation_load_json_schema(schema)
            data_dict[u'schema'] = schema_json

        return data_dict

    def before_create(self, context, resource):
        if _data_dict_is_resource(resource):
            _giftless_upload(context, resource)
            _update_resource_last_modified_date(resource)
            logic.validate_resource_upload_fields(context, resource)
            context["_resource_create_call"] = True
        return self._process_schema_fields(resource)

    def before_update(self, context, current, resource):
        if _data_dict_is_resource(resource):
            _giftless_upload(context, resource, current=current)
            _update_resource_last_modified_date(resource, current=current)
            logic.validate_resource_upload_fields(context, resource)
        return resource

    def before_show(self, resource):
        if _data_dict_is_resource(resource):
            return logic.update_filename_in_resource_url(resource)

    def after_upload(self, context, resource_dict, dataset_dict):
        if "schema" in resource_dict:
            try:
                logic.populate_data_dictionary_from_schema(context, resource_dict)
            except Exception:
                log.exception(
                    "Error in background task auto populating {} data dictionary. "
                    "Failing silently to avoid problems downstream".format(
                        resource_dict.get("id", "")
                    )
                )

    # IAuthenticator
    def identify(self):
        """
        Allows requests to be sent "on behalf" of a substitute user for sysadmins only. This is
        done by setting a HTTP Header in the requests "CKAN-Substitute-User" to be the
        username or user id of another CKAN user.

        Before that happens, OAuth2 access_token is being sought and validated if found.
        """
        if auth_logic.access_token_present_and_valid_and_user_authorized():
            return

        initialize_g_userobj_using_private_core_ckan_method()
        is_sysadmin = toolkit.g.userobj and toolkit.g.userobj.sysadmin
        substitute_user_id = toolkit.request.headers.get('CKAN-Substitute-User')

        if is_sysadmin and substitute_user_id:
            return auth.substitute_user(substitute_user_id)

    def after_saml2_login(self, resp, saml_attributes):
        user_obj = toolkit.g.userobj
        custom_user_profile.read_saml_profile(user_obj, saml_attributes)

        return resp

    # IMiddleware
    def make_middleware(self, app, config):

        @app.errorhandler(auth_logic.OAuth2AuthenticationError)
        def handle_oauth2_authentication_error(error):
            return auth_logic.create_response("Authentication error", error.message, 401)

        @app.errorhandler(auth_logic.OAuth2AuthorizationError)
        def handle_oauth2_authorization_error(error):
            return auth_logic.create_response("Authorization error", error.message, 403)

        return app


class UNAIDSReclineView(ReclineViewBase):
    """
    This override of the recline view plugin allows data explorers to be auto
    created for geojson files.
    """

    def info(self):
        return {
            "name": "unaids_recline_view",
            "title": "Data Explorer",
            "filterable": True,
            "icon": "table",
            "requires_datastore": False,
            "default_title": p.toolkit._("Data Explorer"),
        }

    def can_view(self, data_dict):
        resource = data_dict["resource"]

        if resource.get(
                "datastore_active"
        ) or "_datastore_only_resource" in resource.get("url", ""):
            return True
        resource_format = resource.get("format", None)

        if resource_format:
            return resource_format.lower() in ["csv", "xls", "xlsx", "tsv", "geojson"]
        else:
            return False


def _data_dict_is_resource(data_dict):
    return not (
            "creator_user_id" in data_dict
            or "owner_org" in data_dict
            or "resources" in data_dict
            or data_dict.get("type") == "dataset"
    )


def _giftless_upload(context, resource, current=None):
    attached_file = resource.pop("upload", None)
    if attached_file:
        if type(attached_file) == FlaskFileStorage:
            dataset_id = resource.get("package_id")
            if not dataset_id:
                dataset_id = current["package_id"]
            dataset = get_action("package_show")(context, {"id": dataset_id})
            dataset_name = dataset["name"]
            org_name = dataset.get("organization", {}).get("name")
            authz_token = _get_upload_authz_token(context, dataset_name, org_name)
            lfs_client = LfsClient(
                lfs_server_url=blobstorage_helpers.server_url(),
                auth_token=authz_token,
                transfer_adapters=["basic"],
            )
            uploaded_file = lfs_client.upload(
                file_obj=attached_file, organization=org_name, repo=dataset_name
            )

            lfs_prefix = blobstorage_helpers.resource_storage_prefix(
                dataset_name, org_name=org_name
            )
            resource.update(
                {
                    "url_type": "upload",
                    "last_modified": datetime.datetime.utcnow(),
                    "sha256": uploaded_file["oid"],
                    "size": uploaded_file["size"],
                    "url": attached_file.filename,
                    "lfs_prefix": lfs_prefix,
                }
            )


def _update_resource_last_modified_date(resource, current=None):
    if current is None:
        current = {}
    for key in ["url_type", "lfs_prefix", "sha256", "size", "url"]:
        current_value = current.get(key, "")
        resource_value = resource.get(key, "")
        if current_value != resource_value:
            resource["last_modified"] = datetime.datetime.utcnow()
            return


def _get_upload_authz_token(context, dataset_name, org_name):
    scope = "obj:{}/{}/*:write".format(org_name, dataset_name)
    authorize = toolkit.get_action("authz_authorize")
    if not authorize:
        raise RuntimeError(
            "Cannot find authz_authorize; Is ckanext-authz-service installed?"
        )
    authz_result = authorize(context, {"scopes": [scope]})
    if not authz_result or not authz_result.get("token", False):
        raise RuntimeError("Failed to get authorization token for LFS server")
    if len(authz_result["granted_scopes"]) == 0:
        error = "You are not authorized to upload this resource."
        log.error(error)
        raise toolkit.NotAuthorized(error)
    return authz_result["token"]
