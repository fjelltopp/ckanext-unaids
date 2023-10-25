import logging

from flask_babel import force_locale

import ckan.authz as authz
from ckan import model, logic
from ckan.common import _
from ckan.lib.helpers import url_for, flash_success
from ckan.lib.mailer import mail_user
from ckan.plugins import toolkit
from ckan.plugins.toolkit import config
from ckanext.ytp_request.helper import get_safe_locale
import ckanext.ytp_request.logic.action.create as ytp_request_action_create
from ckanext.ytp_request.model import MemberRequest

log = logging.getLogger(__name__)

_SUBJECT_MEMBERSHIP_REQUEST = _("New membership request (%(organization)s)")
_MESSAGE_MEMBERSHIP_REQUEST = _("""\
    User %(user)s (%(email)s), %(job_title)s at %(affiliation)s, has requested membership to organization %(organization)s.

    %(link)s

    Best wishes,
    The AIDS Data Repository
    """)


def mail_new_membership_request(locale, admin, group_name, url, user_name, user_email, user_job_title, user_affiliation):
    """
    Overrides the mail_new_membership_request function from ckanext-ytp-request plugin
    """
    with force_locale('en'):
        subject = _SUBJECT_MEMBERSHIP_REQUEST % {
                      'organization': group_name
                  }
        message = _MESSAGE_MEMBERSHIP_REQUEST % {
                      'user': user_name,
                      'email': user_email,
                      'organization': group_name,
                      'link': url,
                      'job_title': user_job_title,
                      'affiliation': user_affiliation
                  }
    try:
        mail_user(admin, subject, message)
    except Exception:
        log.exception("Mail could not be sent")


def _create_member_request(context, data_dict):
    """
    Whole method copied over from ckanext-ytp-request plugin
    Helper to create member request
    """
    role = data_dict.get('role', None)
    if not role:
        raise logic.NotFound
    group = model.Group.get(data_dict.get('group', None))

    if not group or group.type != 'organization':
        raise logic.NotFound

    user = context.get('user', None)

    if authz.is_sysadmin(user):
        raise logic.ValidationError({}, {_("Role"): _(
            "As a sysadmin, you already have access to all organizations")})

    userobj = model.User.get(user)

    member = (model.Session.query(model.Member)
              .filter(model.Member.table_name == "user")
              .filter(model.Member.table_id == userobj.id)
              .filter(model.Member.group_id == group.id).first())

    # If there is a member for this organization and it is NOT deleted. Reuse
    # existing if deleted
    if member:
        if member.state == 'pending':
            message = _(
                "You already have a pending request to the organization")
        elif member.state == 'active':
            message = _("You are already part of the organization")
        # Unknown status. Should never happen..
        elif member.state != 'deleted':
            message = _("Duplicate organization request")
            raise logic.ValidationError({"organization": message}, {_("Organization"): message})
    else:
        member = model.Member(table_name="user", table_id=userobj.id, group=group,
                              group_id=group.id, capacity=role, state='pending')

    # TODO: Is there a way to get language associated to all admins. User table there is nothing as such stored
    locale = get_safe_locale()

    member.state = 'pending'
    member.capacity = role
    member.group = group

    logging.warning("Member's Group ID: " + str(type(member.group_id)))
    logging.warning(repr(member))

    model.Session.add(member)
    # We need to flush since we need membership_id (member.id) already
    model.Session.flush()

    memberRequest = MemberRequest(
        membership_id=member.id, role=role, status="pending", language=locale)
    member_id = member.id
    model.Session.add(memberRequest)
    model.repo.commit()

    fetched_member = model.Session.query(model.Member).filter(
        model.Member.id == member_id
    ).first()
    logging.warning(repr(group))
    logging.warning("Fetched member's group ID: " + str(fetched_member.group_id))

    url = config.get('ckan.site_url', "")
    if url:
        url = url + url_for('member_request.show', mrequest_id=member.id)

    try:
        user_job_title = context["auth_user_obj"].plugin_extras["unaids"]["job_title"]
        user_affiliation = context["auth_user_obj"].plugin_extras["unaids"]["affiliation"]
    except Exception:
        log.exception("Error finding user job title and affiliation")

    if role == 'admin':
        for admin in ytp_request_action_create._get_ckan_admins():
            mail_new_membership_request(
                locale, admin, group.display_name, url, userobj.display_name, userobj.email, user_job_title, user_affiliation)
    else:
        for admin in ytp_request_action_create._get_organization_admins(group.id):
            mail_new_membership_request(
                locale, admin, group.display_name, url, userobj.display_name, userobj.email, user_job_title, user_affiliation)
    flash_success(
        _("Membership request sent to organisation administrator")
    )
    return member


@toolkit.chained_action
def member_request_create(next_action, context, data_dict):
    """
    overrides member_request_create action from ckanext-ytp-request plugin,
    purposely to add job_title and affiliation in the mail sent to the admins
    """
    global user_job_title, user_affiliation
    try:
        user_job_title = context["auth_user_obj"].plugin_extras["unaids"]["job_title"]
        user_affiliation = context["auth_user_obj"].plugin_extras["unaids"]["affiliation"]
    except Exception:
        log.exception("Error finding user job title and affiliation")

    ytp_request_action_create._create_member_request = _create_member_request
    return next_action(context, data_dict)
