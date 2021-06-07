import logging
from flask import Blueprint
from flask.views import MethodView
from ckan import model
from ckan.plugins import toolkit
from ckan.common import _
import ckan.lib.helpers as h
from ckan.plugins.toolkit import request

log = logging.getLogger(__name__)
unaids_dataset_releases = Blueprint(
    u'unaids_dataset_releases',
    __name__
)
SOMETHING_WENT_WRONG_ERROR = \
    _('Something went wrong. Please try again.')
AUTHORIZATION_ERROR = \
    _('You are not authorized to carry out this action')
RELEASE_ALREADY_EXISTS_FOR_ACTIVITY_ERROR = \
    _('A release already exists for this version of the dataset')
RELEASE_NAME_NOT_UNIQUE_ERROR = \
    _('Release names must be unique per dataset')


def _get_context():
    # TODO: confirm all of these fields are needed
    return {
        'model': model,
        'session': model.Session,
        'user': toolkit.c.user,
        'for_view': True,
        'auth_user_obj': toolkit.c.userobj
    }


def list_releases(dataset_type, dataset_id):
    # TODO: confirm this shouldn't be a MethodView Class
    # as we're also referring to it from read_base.html
    dataset = toolkit.get_action('package_show')(
        _get_context(), {'id': dataset_id}
    )
    releases = toolkit.get_action('dataset_version_list')(
        _get_context(), {'dataset_id': dataset_id}
    )
    return toolkit.render(
        'package/releases/list.html',
        {
            'pkg_dict': dataset,
            'dataset_releases': releases
        }
    )


def _get_dataset_and_release(dataset_id):
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
    return dataset, release


def _dataset_release_view(dataset_id, template):
    dataset, release = _get_dataset_and_release(dataset_id)
    return toolkit.render(
        'package/releases/{}.html'.format(template),
        {'pkg_dict': dataset, 'release': release}
    )


class ReleaseView(MethodView):
    def get(self, dataset_type, dataset_id):
        return _dataset_release_view(
            dataset_id, 'create_or_edit'
        )

    def post(self, dataset_type, dataset_id):
        dataset = toolkit.get_action('package_show')(
            _get_context(), {'id': dataset_id}
        )
        # TODO: replace form with ckan form
        name = request.form['name']
        notes = request.form.get('notes')
        release_id = request.args.get('release_id')
        activity_id = request.args.get('activity_id')
        try:
            if release_id:
                release = toolkit.get_action('version_update')(
                    _get_context(),
                    {
                        'package_id': dataset_id,
                        'version_id': release_id,
                        'name': name,
                        'notes': notes
                    })
            else:
                release = toolkit.get_action('dataset_version_create')(
                    _get_context(),
                    {
                        'dataset_id': dataset['id'],
                        'activity_id': activity_id,
                        'name': name,
                        'notes': notes
                    })
        except toolkit.NotAuthorized:
            h.flash_error(AUTHORIZATION_ERROR)
        except toolkit.ValidationError as e:
            validation_error = e.error_dict['message']
            if 'Version already exists for this activity' in validation_error:
                error = RELEASE_ALREADY_EXISTS_FOR_ACTIVITY_ERROR
            elif 'Version names must be unique per dataset' in validation_error:
                error = RELEASE_NAME_NOT_UNIQUE_ERROR
            else:
                error = SOMETHING_WENT_WRONG_ERROR
            h.flash_error(error)
        except Exception as e:
            log.error(e)
            h.flash_error(SOMETHING_WENT_WRONG_ERROR)
        else:
            if request.args.get('release_id'):
                h.flash_success(
                    _('Release {} updated').format(release['name'])
                )
            else:
                h.flash_success(
                    _('Release {} added').format(release['name'])
                )
        return h.redirect_to(
            controller='unaids_dataset_releases',
            action='list_releases',
            dataset_type=dataset['type'],
            dataset_id=dataset['id']
        )


class ReleaseDelete(MethodView):
    def get(self, dataset_type, dataset_id):
        return _dataset_release_view(
            dataset_id, 'delete'
        )

    def post(self, dataset_type, dataset_id):
        dataset, release = _get_dataset_and_release(dataset_id)
        try:
            toolkit.get_action('version_delete')(
                _get_context(), {'version_id': release['id']}
            )
        except toolkit.NotAuthorized:
            h.flash_error(AUTHORIZATION_ERROR)
        except Exception as e:
            log.error(e)
            h.flash_error(SOMETHING_WENT_WRONG_ERROR)
        else:
            h.flash_success(
                _('Release {} deleted').format(release['name'])
            )
        return h.redirect_to(
            controller='unaids_dataset_releases',
            action='list_releases',
            dataset_type=dataset['type'],
            dataset_id=dataset['id']
        )


class ReleaseRestore(MethodView):
    def get(self, dataset_type, dataset_id):
        return _dataset_release_view(
            dataset_id, 'restore'
        )

    def post(self, dataset_type, dataset_id):
        dataset, release = _get_dataset_and_release(dataset_id)
        try:
            toolkit.get_action('dataset_version_restore')(
                _get_context(), {
                    'dataset_id': dataset['id'],
                    'version_id': release['id']
                }
            )
        except toolkit.NotAuthorized:
            h.flash_error(AUTHORIZATION_ERROR)
        except Exception as e:
            log.error(e)
            h.flash_error(SOMETHING_WENT_WRONG_ERROR)
        else:
            h.flash_success(
                _('Release {} restored').format(release['name'])
            )
        return h.redirect_to(
            controller='unaids_dataset_releases',
            action='list_releases',
            dataset_type=dataset['type'],
            dataset_id=dataset['id']
        )


unaids_dataset_releases.add_url_rule(
    u'/<dataset_type>/<dataset_id>/releases',
    view_func=list_releases
)
unaids_dataset_releases.add_url_rule(
    u'/<dataset_type>/<dataset_id>/release',
    view_func=ReleaseView.as_view('release_view')
)
unaids_dataset_releases.add_url_rule(
    u'/<dataset_type>/<dataset_id>/release/delete',
    view_func=ReleaseDelete.as_view('release_delete')
)
unaids_dataset_releases.add_url_rule(
    u'/<dataset_type>/<dataset_id>/release/restore',
    view_func=ReleaseRestore.as_view('release_restore')
)
