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


def list_releases(dataset_type, id):
    dataset = toolkit.get_action('package_show')(
        _get_context(), {'id': id}
    )
    releases = toolkit.get_action('dataset_version_list')(
        _get_context(), {'dataset_id': id}
    )
    return toolkit.render(
        'package/releases/list.html',
        {
            'pkg_dict': dataset,
            'dataset_releases': releases
        }
    )


def _dataset_release_view(dataset_id, template):
    dataset = toolkit.get_action('package_show')(
        _get_context(), {'id': dataset_id}
    )
    if request.args.get('release_id'):
        release_id = request.args.get('release_id')
        release = toolkit.get_action('version_show')(
            _get_context(), {'version_id': release_id}
        )
    else:
        release = None
    return toolkit.render(
        'package/releases/{}'.format(template),
        {'pkg_dict': dataset, 'release': release}
    )


class ReleaseView(MethodView):
    def get(self, dataset_type, id):
        return _dataset_release_view(
            id, 'create_or_edit.html'
        )

    def post(self, dataset_type, id):
        dataset = toolkit.get_action('package_show')(
            _get_context(), {'id': id}
        )
        name = request.form['name']
        notes = request.form.get('notes')
        if 'release_id' in request.args:
            release_id = request.args['release_id']
            release = toolkit.get_action('version_update')(
                _get_context(),
                {
                    'package_id': id,
                    'version_id': release_id,
                    'name': name,
                    'notes': notes
                })
            h.flash_success(
                _('Release {} updated').format(release['name'])
            )
        else:
            activity_id = request.args.get('activity_id')
            release = toolkit.get_action('dataset_version_create')(
                _get_context(),
                {
                    'dataset_id': dataset['id'],
                    'activity_id': activity_id,
                    'name': name,
                    'notes': notes
                }
            )
            h.flash_success(
                _('Release {} added').format(release['name'])
            )
        return h.redirect_to(
            controller='dataset',
            action='read',
            id=dataset['name'],
            release_id=release['id']
        )


class ReleaseDelete(MethodView):
    def get(self, dataset_type, id):
        return _dataset_release_view(id, 'delete.html')

    def post(self, dataset_type, id):
        dataset = toolkit.get_action('package_show')(
            _get_context(), {'id': id}
        )
        release_id = request.args['release_id']
        release = toolkit.get_action('version_delete')(
            _get_context(), {'version_id': release_id}
        )
        h.flash_success(
            _('Release {} deleted').format(release['name'])
        )
        return h.redirect_to(
            controller='dataset',
            action='read',
            id=dataset['name']
        )


class ReleaseRestore(MethodView):
    def get(self, dataset_type, id):
        return _dataset_release_view(id, 'restore.html')

    def post(self, dataset_type, id):
        dataset = toolkit.get_action('package_show')(
            _get_context(), {'id': id}
        )
        release_id = request.args['release_id']
        release = toolkit.get_action('version_show')(
            _get_context(), {'version_id': release_id}
        )
        h.flash_success(
            _('Release {} restored').format(release['name'])
        )
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
