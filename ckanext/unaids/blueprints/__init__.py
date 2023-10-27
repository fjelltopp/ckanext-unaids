from ckanext.unaids.blueprints.svg_map_options import svg_map_options
from ckanext.unaids.blueprints.unaids_dataset_transfer import unaids_dataset_transfer
from ckanext.unaids.blueprints.user_info_blueprint import user_info_blueprint
from ckanext.unaids.blueprints.unaids_dataset_releases import unaids_dataset_releases
from ckanext.unaids.blueprints.login_register_catch import login_register_catch
from ckanext.unaids.blueprints.profile_editor_data_receiver import profile_editor_data_receiver
from ckanext.unaids.blueprints.validate_user_affiliation import validate_user_affiliation
from ckanext.unaids.blueprints.members_list import members_list

blueprints = [
    unaids_dataset_transfer,
    user_info_blueprint,
    unaids_dataset_releases,
    svg_map_options,
    login_register_catch,
    profile_editor_data_receiver,
    validate_user_affiliation,
    members_list,
]
