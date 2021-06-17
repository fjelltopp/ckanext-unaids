from ckanext.unaids.blueprints.unaids_blueprint import unaids_blueprint
from ckanext.unaids.blueprints.unaids_dataset_transfer import unaids_dataset_transfer
from ckanext.unaids.blueprints.user_info_blueprint import user_info_blueprint
from ckanext.unaids.blueprints.unaids_dataset_releases import unaids_dataset_releases

blueprints = [
    unaids_blueprint,
    unaids_dataset_transfer,
    user_info_blueprint,
    unaids_dataset_releases
]
