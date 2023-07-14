import json

from flask import Blueprint, redirect, request, jsonify
import requests
from ckan.common import _, g
from ckan.lib.helpers import url_for
from ckan.plugins import toolkit

from urllib.parse import urlparse, urlencode

import jwt

ape_data_receiver = Blueprint("ape_data_receiver", __name__)

parsed_url = urlparse(toolkit.config.get('ckanext.saml2auth.idp_metadata.remote_url'))
auth0_domain = parsed_url.scheme + "://" + parsed_url.netloc
client_id = toolkit.config.get('ape_client_id')
client_secret = toolkit.config.get('ape_client_secret')
redirect_url = toolkit.config.get('ape_callback_url')
state = toolkit.config.get('ape_state')

@ape_data_receiver.route('/ape_data_receiver', methods=['GET'])
def receive():
    if not g.user:
        return toolkit.abort(403, _('You must be logged in to access this page'))
    else:
        base_url = auth0_domain + "/authorize"
        query_params = {
            "scope": "openid profile email user_metadata jobtitle affiliation",
            "response_type": "code",
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_url,
            "state": state,
        }
        auth_url = base_url + "?" + urlencode(query_params)
        return redirect(auth_url)
@ape_data_receiver.route('/ape_callback', methods=['GET'])
def refresh():
    token_endpoint = f'{auth0_domain}/oauth/token'
    response = requests.post(token_endpoint, json={
        'grant_type': 'authorization_code',
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_url,
        'code': request.args.get('code')
    })

    id_token = response.json()["id_token"]
    decoded_id_token = jwt.decode(id_token, options={"verify_signature": False})
    return decoded_id_token

