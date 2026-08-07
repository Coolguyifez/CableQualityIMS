from flask_login import current_user

from .extensions import db

from .models import Notification, User


def create_notification(

        title,

        message,

        category="General",

        priority="Normal",

        user_id=None,

        link=None

):

    # Notification for one specific user
    if user_id is not None:

        notification = Notification(

            company_id=current_user.company_id,

            user_id=user_id,

            title=title,

            message=message,

            category=category,

            priority=priority,

            link=link

        )

        db.session.add(notification)

    # Notification for all active users in the company
    else:

        users = User.query.filter_by(

            company_id=current_user.company_id,

            is_active=True

        ).all()

        for user in users:

            notification = Notification(

                company_id=current_user.company_id,

                user_id=user.id,

                title=title,

                message=message,

                category=category,

                priority=priority,

                link=link

            )

            db.session.add(notification)

    db.session.commit()

