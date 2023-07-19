import json

from flask import Blueprint, redirect, request, flash
import requests
from ckan.common import _, g
from ckan.lib.helpers import url_for
from ckan.plugins import toolkit

from urllib.parse import urlparse

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

ape_data_receiver = Blueprint("ape_data_receiver", __name__)



@ape_data_receiver.route('/ape_data_receiver', methods=['GET'])
def receive():
    if not g.user:
        return toolkit.abort(403, _('You must be logged in to access this page'))
    else:
        flash(_('User profile successfully saved, you need to log in again to see the changes.'))
        return redirect(url_for('user.edit', id=g.user))


