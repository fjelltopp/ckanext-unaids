import ckan.plugins.toolkit as toolkit
from flask import Blueprint, Response
from io import StringIO
import logging
import pandas

log = logging.getLogger(__name__)
members_list = Blueprint(
    'members_list',
    __name__
)


@members_list.route('/organization/members/<group_id>/download')
def org_member_download(group_id):
    try:
        toolkit.check_access(
            'group_edit_permissions',
            {'user': toolkit.g.user},
            {'id': group_id}
        )
        memberships = toolkit.get_action("member_list")(
            {},
            {"id": group_id, "object_type": "user"}
        )
    except toolkit.ObjectNotFound:
        toolkit.abort(404, toolkit._('Group not found'))
    except toolkit.NotAuthorized:
        toolkit.abort(
            403,
            toolkit._(f'User {toolkit.g.user} not '
                      f'authorized to download members of {group_id}')
        )
    user_list = []
    for member in memberships:
        user_dict = toolkit.get_action("user_show")(
            {'keep_email': True},
            {"id": member[0]}
        )
        user_list.append({
            toolkit._("Username"): user_dict.get('name'),
            toolkit._("Full Name"): user_dict.get('fullname'),
            toolkit._("Email"): user_dict.get('email'),
            toolkit._("Affiliation"): user_dict.get("affiliation"),
            toolkit._("Job Title"): user_dict.get('job_title'),
            toolkit._("ADR Org"): group_id,
            toolkit._("ADR Org Role"): member[2]
        })
    df = pandas.DataFrame.from_records(user_list)
    csv = df.to_csv(index=False)
    output = StringIO()
    output.write(csv)
    output.seek(0)
    filename = toolkit._(f"{group_id}_adr_membership.csv")
    return Response(
                output,
                mimetype="text/csv",
                headers={"Content-disposition":
                         f"attachment; filename={filename}"}
            )
