import ckanext.ytp_request.mail as mail
from ckanext.ytp_request.model import MemberRequest
from ckan.lib.mailer import mail_user
from ckan import model, logic
import ckan.authz as authz
from ckanext.ytp_request.helper import get_safe_locale
from ckan.lib.helpers import url_for, flash_success
import logging
from ckan.common import _
from ckan.plugins.toolkit import config
from flask_babel import force_locale

def unaids_create_member_request(context, data_dict):
    """ Helper to create member request """
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
    extras = userobj.plugin_extras['unaids']
    user_job_title = extras.get('job_title', '')
    user_affiliation = extras.get('affiliation', '')

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
            raise logic.ValidationError({"organization": _(
                "Duplicate organization request")}, {_("Organization"): message})
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
    # Locale should be admin locale since mail is sent to admins
    if role == 'admin':
        for admin in _get_ckan_admins():
            send_mail_for_new_membership_request(
                locale, admin, group.display_name, url, userobj.display_name, userobj.email, user_job_title, user_affiliation)
    else:
        for admin in _get_organization_admins(group.id):
            send_mail_for_new_membership_request(
                locale, admin, group.display_name, url, userobj.display_name, userobj.email, user_job_title, user_affiliation)
    flash_success(
        _("Membership request sent to organisation administrator")
    )
    return member

def send_mail_for_new_membership_request(locale, admin, group_name, url, user_name, user_email, user_job_title, user_affiliation):
    with force_locale('en'):
        subject = _SUBJECT_MEMBERSHIP_REQUEST() % {
            'organization': group_name
        }
        message = _MESSAGE_MEMBERSHIP_REQUEST() % {
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

def _SUBJECT_MEMBERSHIP_REQUEST():
    return _(
            "New membership request (%(organization)s)")

def _MESSAGE_MEMBERSHIP_REQUEST():
    return _(
        """\
        User %(user)s (%(email)s), %(job_title)s at %(affiliation)s, has requested membership to organization %(organization)s.

        %(link)s

        Best wishes,
        The AIDS Data Repository
        """
    )


def _get_organization_admins(group_id):
    admins = set(
        model.Session.query(model.User)
        .join(model.Member, model.User.id == model.Member.table_id)
        .filter(model.Member.table_name == "user")
        .filter(model.Member.group_id == group_id)
        .filter(model.Member.state == 'active')
        .filter(model.Member.capacity == 'admin')
        .filter(model.User.email != '')
    )

    admins.update(set(
        model.Session.query(model.User)
        .filter(model.User.sysadmin is True)
        .filter(model.User.email != '')
        )
    )
    return admins