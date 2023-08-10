from flask import Blueprint, redirect
from ckan.common import _, g
from ckan.lib.helpers import url_for
from ckan.plugins import toolkit


profile_editor_data_receiver = Blueprint("profile_editor_data_receiver", __name__)


@profile_editor_data_receiver.route('/profile_editor_data_receiver', methods=['GET'])
def receive():
    if not g.user:
        return toolkit.abort(403, _('You must be logged in to access this page'))
    else:
        toolkit.h.flash_success(_('User profile successfully saved, you need to log in again to see the changes.'))
        return redirect(url_for('user.edit', id=g.user))
