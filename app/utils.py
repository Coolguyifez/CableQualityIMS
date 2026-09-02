from flask import current_app
from flask_login import current_user

from .extensions import db

from .models import (
    Notification,
    User,
    PushSubscription
)

from .push_utils import send_push_notification


def create_notification(
    title,
    message,
    category="General",
    priority="Normal",
    user_id=None,
    link=None
):

    # ------------------------------------
    # Determine recipients
    # ------------------------------------

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


    # ------------------------------------
    # Create database notifications
    # ------------------------------------

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


    # Save in-app notifications first
    db.session.commit()


    # ------------------------------------
    # Send browser/device push notifications
    # ------------------------------------

    for user in users:

        # Master notification switch
        if not user.notification_enabled:
            continue


        # --------------------------------
        # Category preferences
        # --------------------------------

        if category == "Inspection":

            if not user.inspection_notification:
                continue

        elif category == "Deviation":

            if not user.deviation_notification:
                continue

        elif category == "CAPA":

            if not user.capa_notification:
                continue


        # --------------------------------
        # Get user's push subscriptions
        # --------------------------------

        subscriptions = PushSubscription.query.filter_by(

            user_id=user.id,

            company_id=user.company_id

        ).all()


        # --------------------------------
        # Send push to each device
        # --------------------------------

        for subscription in subscriptions:

            try:

                send_push_notification(

                    subscription=subscription,

                    title=title,

                    message=message,

                    link=link,

                    priority=priority

                )

            except Exception as e:

                # Push notification failure must
                # never break the main application.

                current_app.logger.error(

                    f"Push notification failed for "
                    f"for subscription {subscription.id}: {e}",

                    exc_info=True

                )

                # Make sure a failed push does not
                # leave the SQLAlchemy transaction
                # in a broken state.

                db.session.rollback()
                
                continue
