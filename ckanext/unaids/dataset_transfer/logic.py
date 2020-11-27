from datetime import datetime
import logging

from ckan import model, logic, authz
import ckan.plugins.toolkit as toolkit
from ckanext.unaids.dataset_transfer.model import (
    DatasetTransferRequest,
    STATUS_EMAILED,
    STATUS_EMAIL_FAILED
)

log = logging.getLogger(__name__)


def send_dataset_transfer_emails(dataset_id, recipient_org_id):

    recipient_org = toolkit.get_action('organization_show')(
        context, {'id': recipient_org_id}
    )
    recipient_org_admin_ids = [
        user['id']
        for user in recipient_org['users']
        if user['capacity'] == 'admin'
    ]
    recipient_org_admins = model.Session.query(model.User).filter(
            model.User.id.in_(recipient_org_admin_ids),
            model.User.email.isnot(None)
    ).all()
    user_ids_already_emailed = \
        model.Session.query(DatasetTransferRequest.recipient_user_id).filter(
            model.DatasetTransferRequest.dataset_id == dataset_id,
            model.DatasetTransferRequest.recipient_org_id == recipient_org_id
        ).all()
    users_to_email = filter(
        lambda user: user.id not in user_ids_already_emailed,
        recipient_org_admins
    )

    for user in users_to_email:
        log.warn('Emailing {} - {}'.format(user.name, user.email))
        try:
            # TODO: send email
            status = STATUS_EMAILED
        except:
            # TODO: failed
            status = STATUS_EMAIL_FAILED

        model.Session.add(DatasetTransferRequest(
            dataset_id=dataset_id,
            recipient_org_id=recipient_org_id,
            recipient_user=user.id,
            status=status
        ))
        model.repo.commit()
