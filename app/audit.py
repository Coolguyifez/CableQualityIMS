from flask_login import current_user
from .extensions import db
from .models import AuditLog


def log_activity(
    module,
    action,
    description=""
):

    company_id = None
    user_id = None

    if current_user.is_authenticated:

        user_id = current_user.id
        company_id = current_user.company_id

    log = AuditLog(

        company_id=company_id,

        user_id=user_id,

        module=module,

        action=action,

        description=description

    )

    db.session.add(log)