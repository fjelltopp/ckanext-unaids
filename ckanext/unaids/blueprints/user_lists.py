import ckan.plugins.toolkit as toolkit
from flask import Blueprint, Response
from io import StringIO
import logging
import pandas
import json

log = logging.getLogger(__name__)
user_lists = Blueprint(
    'user_lists',
    __name__
)


def org_member_download(group_id):
    memberships = toolkit.get_action("member_list")(
        {},
        {"id": group_id, "object_type": "user"}
    )
    user_list = []

    for member in memberships:
        user_dict = toolkit.get_action("user_show")(
            {'keep_email': True},
            {"id": member[0]}
        )
        user_list.append({
            "username": user_dict.get('name'),
            "full_name": user_dict.get('fullname'),
            "email": user_dict.get('email'),
            "affiliation": user_dict.get("affiliation"),
            "job_title": user_dict.get('job_title'),
            "adr_org": group_id,
            "adr_org_role": member[2]
        })

    df = pandas.DataFrame.from_records(user_list)
    csv = df.to_csv(index=False)

    output = StringIO()
    output.write(csv)
    output.seek(0)

    return Response(
                output,
                mimetype="application/json",
                headers={"Content-disposition":
                         "attachment; filename=org_members.csv"}
            )


user_lists.add_url_rule(
    '/organization/members/<group_id>/download',
    view_func=org_member_download
)
