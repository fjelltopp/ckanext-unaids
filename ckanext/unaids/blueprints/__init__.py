from ckanext.unaids.blueprints.svg_map_options import svg_map_options
from ckanext.unaids.blueprints.unaids_dataset_transfer import unaids_dataset_transfer
from ckanext.unaids.blueprints.user_info_blueprint import user_info_blueprint
from ckanext.unaids.blueprints.unaids_dataset_releases import unaids_dataset_releases
from ckanext.unaids.blueprints.user_affiliation import user_affiliation

blueprints = [
    unaids_dataset_transfer,
    user_info_blueprint,
    unaids_dataset_releases,
    svg_map_options,
    user_affiliation,
]
