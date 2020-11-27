from sqlalchemy import Column, MetaData, types
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from ckan.lib.base import model

Base = declarative_base()
metadata = MetaData()


STATUS_EMAILED = "emailed"
STATUS_EMAIL_FAILED = "email_failed"
STATUS_ACCEPTED = "accepted"


class DatasetTransferRequest(Base):
    """
    Represents the status of email communication of dataset transfers to organizations,
    each row is a user who has been emailed regarding a specific dataset transfer
    """
    __tablename__ = 'dataset_transfer_request'

    id = Column(types.Integer, primary_key=True)
    dataset_id = Column(types.UnicodeText)
    recipient_org_id = Column(types.UnicodeText)
    recipient_user_id = Column(types.UnicodeText)
    status = Column(types.UnicodeText, required=True)
    status_last_changed_timestamp = Column(types.DateTime, onupdate=func.now())


def init_tables():
    Base.metadata.create_all(model.meta.engine)
