from ckan import model
from ckan.plugins import toolkit
from ckan.tests import factories as ckan_factories
from ckanext.unaids.dataset_transfer.model import tables_exists, init_tables
from ckanext.versions.logic.dataset_version_action import dataset_version_create


def unaids_db_setup():
    if not tables_exists():
        init_tables()


def get_context(user):
    return {
        'model': model,
        'user': user if isinstance(user, str) else user['name']
    }


def create_dataset_with_releases(user, number_of_releases=5):
    org = ckan_factories.Organization(user=user)
    dataset = ckan_factories.Dataset(user=user, owner_org=org['id'])
    releases = []
    for x in range(number_of_releases):
        activities = toolkit.get_action('package_activity_list')(
            get_context(user),
            {'id': dataset['id']}
        )
        releases.append(dataset_version_create(
            get_context(user),
            {
                'dataset_id': dataset['id'],
                'activity_id': activities[0]['id'],
                'name': 'release-{}'.format(x),
                'notes': 'Test Notes'
            }
        ))
        toolkit.get_action('package_patch')(
            get_context(user),
            {
                'id': dataset['id'],
                'title': 'updated-title-{}'.format(x)
            }
        )
    return dataset, releases


def create_version(dataset_id, user, version_name="Default Name"):
    return dataset_version_create(
        get_context(user),
        {
            "dataset_id": dataset_id,
            "name": version_name
        }
    )
