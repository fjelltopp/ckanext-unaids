from sqlalchemy import Column, types, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

from ckan.model import meta
from ckan.model.meta import metadata

Base = declarative_base(metadata=metadata)

STATUS_EMAILED = "emailed"
STATUS_EMAIL_FAILED = "email_failed"
STATUS_ACCEPTED = "accepted"


class DatasetTransferRequest(Base):
    """
    Represents the status of email communication of dataset transfers to organizations,
    each row is a user who has been emailed regarding a specific dataset transfer
    """
    __tablename__ = 'dataset_transfer_request'

    id = Column(types.Integer, primary_key=True, nullable=False)
    dataset_id = Column(types.UnicodeText, nullable=False)
    recipient_org_id = Column(types.UnicodeText, nullable=False)
    recipient_user_id = Column(types.UnicodeText, nullable=False)
    status = Column(types.UnicodeText, nullable=False)
    status_last_changed_timestamp = Column(
        types.DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    extend_existing = True


def init_tables():
    DatasetTransferRequest.__table__.create(bind=meta.engine, checkfirst=True)


def tables_exists():
    if meta.engine is None:
        return False
    inspector = inspect(meta.engine)
    return DatasetTransferRequest.__tablename__ in inspector.get_table_names()
