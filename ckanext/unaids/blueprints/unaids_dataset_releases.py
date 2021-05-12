from datetime import datetime
from flask import Blueprint
from flask.views import MethodView
from ckan.plugins import toolkit
from ckan.common import _
import ckan.lib.helpers as h
from ckan.plugins.toolkit import request


unaids_dataset_releases = Blueprint(
    u'unaids_dataset_releases',
    __name__
)


# TODO: fetch this from the db using request.args['release_id']
TEMP_RELEASE = {
    'name': 'TODO',
    'notes': 'TODO'
}


def list_releases(dataset_type, id):
    dataset = toolkit.get_action('package_show')({}, {'id': id})
    dataset_releases = [
        {
            'id': 'release_{}'.format(x),
            'name': 'Release {}'.format(x),
            'notes': 'Notes for release {}'.format(x),
            'author': 'Manoj Nathwani',
            'created': datetime.now().strftime('%d/%m/%Y %H:%M'),
        }
        for x in range(1, 16)
    ]
    return toolkit.render(
        'package/releases/list.html',
        {
            'pkg_dict': dataset,
            'dataset_releases': dataset_releases
        }
    )


class ReleaseView(MethodView):
    def get(self, dataset_type, id):
        dataset = toolkit.get_action('package_show')({}, {'id': id})
        release = {}
        if 'release_id' in request.args:
            release.update(TEMP_RELEASE)
        return toolkit.render(
            'package/releases/create_or_edit.html',
            {
                'pkg_dict': dataset,
                'release': release
            }
        )

    def post(self, dataset_type, id):
        if 'release_id' in request.args:
            release = TEMP_RELEASE  # TODO
            h.flash_success(_(
                'Release {} updated'.format(release['name'])
            ))
            return h.redirect_to(
                controller='dataset',
                action='read',
                id=id
            )
        else:
            release = TEMP_RELEASE  # TODO
            h.flash_success(_(
                'Release {} added'.format(release['name'])
            ))
            return h.redirect_to(
                controller='dataset',
                action='read',
                id=id
            )


class ReleaseDelete(MethodView):
    def get(self, dataset_type, id):
        dataset = toolkit.get_action('package_show')({}, {'id': id})
        release = TEMP_RELEASE  # TODO
        return toolkit.render(
            'package/releases/delete.html',
            {
                'pkg_dict': dataset,
                'release': release
            }
        )

    def post(self, dataset_type, id):
        release = TEMP_RELEASE  # TODO
        h.flash_success(_(
            'Release {} deleted'.format(release['name'])
        ))
        return h.redirect_to(
            controller='dataset',
            action='read',
            id=id
        )


class ReleaseRestore(MethodView):
    def get(self, dataset_type, id):
        dataset = toolkit.get_action('package_show')({}, {'id': id})
        release = TEMP_RELEASE  # TODO
        return toolkit.render(
            'package/releases/restore.html',
            {
                'pkg_dict': dataset,
                'release': release
            }
        )

    def post(self, dataset_type, id):
        release = TEMP_RELEASE  # TODO
        h.flash_success(_(
            'Release {} restored'.format(release['name'])
        ))
        return h.redirect_to(
            controller='dataset',
            action='read',
            id=id
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
