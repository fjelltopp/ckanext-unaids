from flask import Blueprint, redirect
from ckan.common import _, g
from ckan.lib.helpers import url_for
from ckan.plugins import toolkit


ape_data_receiver = Blueprint("ape_data_receiver", __name__)

@ape_data_receiver.route('/ape_data_receiver', methods=['GET'])
def receive():
    if not g.user:
        return toolkit.abort(403, _('You must be logged in to access this page'))
    else:
        toolkit.h.flash_success(_('User profile successfully saved. You need to log in again to see the changes.'))

        return redirect(url_for('user.edit', id=g.user))
