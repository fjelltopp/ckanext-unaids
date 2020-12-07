import logging

from ckan import model
import ckan.plugins.toolkit as toolkit
from ckan.lib import mailer
from ckan.lib.base import render_jinja2
from ckan.common import config, _
from ckanext.unaids.dataset_transfer.model import (
    DatasetTransferRequest,
    STATUS_EMAILED,
    STATUS_EMAIL_FAILED
)

log = logging.getLogger(__name__)


def get_org_admins_with_email_addresses(org, exclude_user_ids):
    try:
        org_admin_ids = [
            user['id']
            for user in org['users']
            if user['capacity'] == 'admin'
        ]
    except KeyError:
        raise ValueError('{} {} {}'.format(
            _('Organization'),
            org['name'],
            _('has no users to accept this transfer')
        ))
    return model.Session.query(model.User).filter(
        model.User.id.in_(org_admin_ids),
        ~model.User.id.in_(exclude_user_ids),
        model.User.email.isnot(None)
    ).all()


def send_dataset_transfer_emails(dataset_id, recipient_org_id):

    dataset = toolkit.get_action('package_show')(
        {'ignore_auth': True}, {'id': dataset_id}
    )
    dataset_org = toolkit.get_action('organization_show')(
        {'ignore_auth': True},
        {
            'id': dataset['owner_org'],
            'include_users': True
        }
    )
    recipient_org = toolkit.get_action('organization_show')(
        {'ignore_auth': True},
        {
            'id': recipient_org_id,
            'include_users': True
        }
    )
    dataset_url = toolkit.url_for(
        'dataset.read',
        id=dataset['name']
    )
    accept_transfer_url = toolkit.url_for(
        'unaids_dataset_transfer.process_dataset_transfer',
        dataset_id=dataset['id']
    )

    user_ids_already_emailed = \
        model.Session.query(DatasetTransferRequest.recipient_user_id).filter(
            DatasetTransferRequest.dataset_id == dataset_id,
            DatasetTransferRequest.recipient_org_id == recipient_org_id
        ).all()
    users_to_email = get_org_admins_with_email_addresses(
        org=recipient_org,
        exclude_user_ids=user_ids_already_emailed
    )

    emails_succeeded = []
    for user in users_to_email:
        try:
            subject = '{} {}'.format(dataset['title'], _('Dataset Transfer'))
            body = render_jinja2(
                'email/dataset_transfer.txt',
                extra_vars={
                    'user': user,
                    'dataset': dataset,
                    'dataset_org': dataset_org,
                    'recipient_org': recipient_org,
                    'dataset_url': config.get('ckan.site_url') + dataset_url,
                    'accept_transfer_url': config.get('ckan.site_url') + accept_transfer_url
                }
            )
            mailer.mail_user(user, subject, body)
            status = STATUS_EMAILED
            emails_succeeded.append(user)
        except mailer.MailerException:
            status = STATUS_EMAIL_FAILED
            log.error('Sending email for DatasetTransferRequest failed for user {} dataset_id {}'.format(
                user.id, dataset['id']
            ))
        model.Session.add(DatasetTransferRequest(
            dataset_id=dataset_id,
            recipient_org_id=recipient_org_id,
            recipient_user_id=user.id,
            status=status
        ))
        model.repo.commit()
        assert emails_succeeded, \
            'All DatasetTransferRequest emails failed for dataset {}'.format(
                dataset['id']
            )
        )
