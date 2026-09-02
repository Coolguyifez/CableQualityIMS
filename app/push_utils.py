import json
import os

from pywebpush import webpush, WebPushException

from .extensions import db


def get_vapid_public_key():
    return os.environ.get("VAPID_PUBLIC_KEY")


def send_push_notification(
    subscription,
    title,
    message,
    link=None,
    priority="Normal"
):

    payload = {
        "title": title,
        "message": message,
        "link": link,
        "priority": priority
    }

    subscription_info = {
        "endpoint": subscription.endpoint,
        "keys": {
            "p256dh": subscription.p256dh,
            "auth": subscription.auth
        }
    }

    try:

        webpush(
            subscription_info=subscription_info,
            data=json.dumps(payload),
            vapid_private_key=os.environ.get(
                "VAPID_PRIVATE_KEY"
            ),
            vapid_claims={
                "sub": os.environ.get(
                    "VAPID_EMAIL",
                    "mailto:ikukaiwee@gmail.com"
                )
            },
            timeout=5
        )

        return True

    except WebPushException as e:

        print(
            "Push notification failed:",
            e
        )

        if e.response is not None:

            status_code = e.response.status_code

            print(
                "Push response status:",
                status_code
            )

            try:
                print(
                    "Response body:",
                    e.response.text
                )
            except Exception:
                pass

            # Subscription is no longer valid
            if status_code in [400, 404, 410]:

                try:

                    db.session.delete(subscription)
                    db.session.commit()

                    print(
                        "Invalid push subscription removed."
                    )

                except Exception:

                    db.session.rollback()

        return False

    except Exception as e:

        print(
            "Unexpected push notification error:",
            e
        )

        return False
