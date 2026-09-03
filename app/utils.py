from flask import current_app
from flask_login import current_user

from .extensions import db
from .models import Notification, User, PushSubscription
from .push_utils import send_push_notification


def create_notification(
    title,
    message,
    category="General",
    priority="Normal",
    user_id=None,
    link=None
):

    if user_id is not None:

        users = User.query.filter_by(
            id=user_id,
            company_id=current_user.company_id,
            is_active=True
        ).all()

    else:

        users = User.query.filter_by(
            company_id=current_user.company_id,
            is_active=True
        ).all()

    # -----------------------------------------
    # FILTER USERS BY NOTIFICATION PREFERENCES
    # -----------------------------------------

    eligible_users = []

    for user in users:

        # Master notification switch
        if not user.notification_enabled:
            continue

        # Category-specific notification switch
        if category == "Inspection":

            if not user.inspection_notification:
                continue

        elif category == "Deviation":

            if not user.deviation_notification:
                continue

        elif category == "CAPA":

            if not user.capa_notification:
                continue

        eligible_users.append(user)

    # -----------------------------------------
    # CREATE DATABASE NOTIFICATIONS
    # ONLY FOR USERS WHO ALLOW THEM
    # -----------------------------------------

    for user in eligible_users:

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

    # -----------------------------------------
    # SEND PUSH NOTIFICATIONS
    # -----------------------------------------

    for user in eligible_users:

        subscriptions = PushSubscription.query.filter_by(
            user_id=user.id,
            company_id=user.company_id
        ).all()

        for subscription in subscriptions:

            try:

                send_push_notification(
                    subscription=subscription,
                    title=title,
                    message=message,
                    link=link,
                    priority=priority
                )

            except Exception:

                current_app.logger.exception(
                    "Push notification failed for subscription %s",
                    subscription.id
                )

                try:
                    db.session.rollback()
                except Exception:
                    pass
