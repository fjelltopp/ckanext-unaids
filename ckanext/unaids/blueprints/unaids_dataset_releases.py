from datetime import datetime
from flask import Blueprint
from flask.views import MethodView
from ckan import model
from ckan.plugins import toolkit
from ckan.common import _
import ckan.lib.helpers as h
from ckan.plugins.toolkit import request

unaids_dataset_releases = Blueprint(
    u'unaids_dataset_releases',
    __name__
)


def _get_context():
    return {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user,
        'for_view': True,
        'auth_user_obj': toolkit.c.userobj
    }


def get_dataset_releases():
    # TODO: replace with database request
    return [
        {
            'id': 'resource-id-{}'.format(x),
            'dataset_id': 'dataset-id-{}'.format(x),
            'activity_id': 'activity-id-{}'.format(x),
            'name': 'V{}.0'.format(x),
            'description': 'Notes about release {}'.format(x),
            'creator_user': toolkit.c.user,
            'created': datetime.now()
        }
        for x in range(1, 16)
    ]


def get_dataset_release(id):
    # TODO: replace with database request
    return [
        x for x in get_dataset_releases()
        if x['id'] == id
    ][0]


def create_release(activity_id, name, description):
    # TODO: replace with database request
    return get_dataset_releases()[0]


def list_releases(dataset_type, id):
    dataset = toolkit.get_action('package_show')(
        _get_context(), {'id': id}
    )
    return toolkit.render(
        'package/releases/list.html',
        {
            'pkg_dict': dataset,
            'dataset_releases': get_dataset_releases()
        }
    )


class ReleaseView(MethodView):
    def get(self, dataset_type, id):
        dataset = toolkit.get_action('package_show')(
            _get_context(), {'id': id}
        )
        release = {}
        if 'release_id' in request.args:
            release_id = request.args['release_id']
            release = get_dataset_release(release_id)
            release.update(release)
        return toolkit.render(
            'package/releases/create_or_edit.html',
            {
                'pkg_dict': dataset,
                'release': release
            }
        )

    def post(self, dataset_type, id):
        dataset = toolkit.get_action('package_show')(
            _get_context(), {'id': id}
        )
        if 'release_id' in request.args:
            release_id = request.args['release_id']
            release = get_dataset_release(release_id)
            h.flash_success(_(
                'Release {} updated'.format(release['name'])
            ))
        else:
            if 'activity_id' in request.args:
                activity_id = request.args['activity_id']
            else:
                activity_id = toolkit.get_action(
                    'package_activity_list')(
                    _get_context(), {'id': dataset['id']}
                )[0]['id']
            name = request.form['name']
            assert len(name), 'Name must be set'
            description = request.form.get('description', None)
            release = create_release(activity_id, name, description)
            h.flash_success(_(
                'Release {} added'.format(release['name'])
            ))
        return h.redirect_to(
            controller='dataset',
            action='read',
            id=dataset['name'],
            release_id=release['id']
        )


class ReleaseDelete(MethodView):
    def get(self, dataset_type, id):
        dataset = toolkit.get_action('package_show')(
            _get_context(), {'id': id}
        )
        release_id = request.args['release_id']
        release = get_dataset_release(release_id)
        return toolkit.render(
            'package/releases/delete.html',
            {
                'pkg_dict': dataset,
                'release': release
            }
        )

    def post(self, dataset_type, id):
        dataset = toolkit.get_action('package_show')(
            _get_context(), {'id': id}
        )
        release_id = request.args['release_id']
        release = get_dataset_release(release_id)
        h.flash_success(_(
            'Release {} deleted'.format(release['name'])
        ))
        return h.redirect_to(
            controller='dataset',
            action='read',
            id=dataset['name']
        )


class ReleaseRestore(MethodView):
    def get(self, dataset_type, id):
        dataset = toolkit.get_action('package_show')(
            _get_context(), {'id': id}
        )
        release_id = request.args['release_id']
        release = get_dataset_release(release_id)
        return toolkit.render(
            'package/releases/restore.html',
            {
                'pkg_dict': dataset,
                'release': release
            }
        )

    def post(self, dataset_type, id):
        dataset = toolkit.get_action('package_show')(
            _get_context(), {'id': id}
        )
        release_id = request.args['release_id']
        release = get_dataset_release(release_id)
        h.flash_success(_(
            'Release {} restored'.format(release['name'])
        ))
        return h.redirect_to(
            controller='dataset',
            action='read',
            id=dataset['name'],
            release_id=release['id']
        )


unaids_dataset_releases.add_url_rule(
    u'/<dataset_type>/<id>/releases',
    view_func=list_releases
)
unaids_dataset_releases.add_url_rule(
    u'/<dataset_type>/<id>/release',
    view_func=ReleaseView.as_view('release_view')
)
unaids_dataset_releases.add_url_rule(
    u'/<dataset_type>/<id>/release/delete',
    view_func=ReleaseDelete.as_view('release_delete')
)
unaids_dataset_releases.add_url_rule(
    u'/<dataset_type>/<id>/release/restore',
    view_func=ReleaseRestore.as_view('release_restore')
)
