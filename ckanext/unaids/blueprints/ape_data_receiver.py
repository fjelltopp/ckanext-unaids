import json

from flask import Blueprint, redirect, request, jsonify
import requests
from ckan.common import _, g
from ckan.lib.helpers import url_for
from ckan.plugins import toolkit

from urllib.parse import urlparse, urlencode



ape_data_receiver = Blueprint("ape_data_receiver", __name__)

@ape_data_receiver.route('/ape_data_receiver', methods=['GET'])
def receive():
    # import pydevd_pycharm
    # pydevd_pycharm.settrace('172.17.0.1', port=9999, stdoutToServer=True, stderrToServer=True)
    if not g.user:
        return toolkit.abort(403, _('You must be logged in to access this page'))
    else:
        parsed_url = urlparse(toolkit.config.get('ckanext.saml2auth.idp_metadata.remote_url'))
        base_url = parsed_url.scheme + "://" + parsed_url.netloc + "/authorize"
        client_id = toolkit.config.get('ape_client_id')
        client_secret = toolkit.config.get('ape_client_secret')
        redirect_url = toolkit.config.get('ape_callback_url')
        state = toolkit.config.get('ape_state')
        audience = url_for('ape_data_receiver.accept', _external=True)
        query_params = {
            "scope": "openid profile email",
            # "audience": audience,
            "response_type": "code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_url,
            "state": state,
            # "prompt": "none"
        }
        auth_url = base_url + "?" + urlencode(query_params)
        silent_response = requests.get(auth_url)

        # return redirect('http://adr.local/user/edit/admin')
        # return jsonify({"message": "Silent authentication initiated.", "args": request.args, "silent_response": silent_response.text})
        return redirect(auth_url)
@ape_data_receiver.route('/ape_callback', methods=['GET'])
def refresh():
    return request.args


@ape_data_receiver.route('/ape_audience', methods=['GET'])
def accept():
    return "ok"
