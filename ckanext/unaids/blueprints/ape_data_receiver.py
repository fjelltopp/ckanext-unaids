import json

from flask import Blueprint, redirect, request, flash
import requests
from ckan.common import _, g
from ckan.lib.helpers import url_for
from ckan.plugins import toolkit

ape_data_receiver = Blueprint("ape_data_receiver", __name__)

auth0_domain = toolkit.config.get('auth0_url')
client_id = toolkit.config.get('ape_client_id')
client_secret = toolkit.config.get('ape_client_secret')
state = toolkit.config.get('ape_state')


def get_mgmt_token():
    payload = f"grant_type=client_credentials&client_id={client_id}" \
              f"&client_secret={client_secret}" \
              f"&audience={auth0_domain}/api/v2/"
    url = f'{auth0_domain}/oauth/token'
    headers = {'content-type': "application/x-www-form-urlencoded"}
    response = requests.post(url, data=payload, headers=headers)
    mgmt_token = response.json().get("access_token")

    return mgmt_token


def get_user_data():
    user_id = request.args.get('user_id')
    # try:
    #     saml_id = toolkit.get_action('user_show')({'ignore_auth': True}, {'id': g.user, 'include_plugin_extras': True})['plugin_extras']['saml_id']
    #     if saml_id:
    #         user_id = saml_id
    # except KeyError:
    #     pass

    if user_id == "":
        flash(_("User ID is empty"), 'error')
        return redirect(url_for('user.edit', id=g.user))

    mgmt_token = get_mgmt_token()
    headers = {
        'Authorization': f'Bearer {mgmt_token}',
        'Content-Type': 'application/json'
    }
    url = f'{auth0_domain}/api/v2/users/{user_id}'
    res_json = requests.get(url, headers=headers).json()

    return res_json

@ape_data_receiver.route('/ape_data_receiver', methods=['GET'])
def receive():
    if not g.user:
        return toolkit.abort(403, _('You must be logged in to access this page'))
    else:
        user_data = get_user_data()
        user_metadata = user_data.get("user_metadata", {})

        user_dict = {
            "id": g.user,
            "email": user_data.get("email", ""),
            "fullname": user_metadata.get("full_name", ""),
            "plugin_extras": {
                "unaids":{
                    "job_title": user_metadata.get("jobtitle", ""),
                    "affiliation": user_metadata.get("orgname", ""),
                }
            }
        }
        context = {
            "user": g.user,
            "ignore_auth": True
        }
        try:
            toolkit.get_action('user_update')(context, user_dict)
        except:
            pass
        return redirect(url_for('user.edit', id=g.user))


