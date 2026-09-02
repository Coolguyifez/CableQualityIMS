import json
import os

from pywebpush import webpush, WebPushException

from .extensions import db


def get_vapid_public_key():

    return os.environ.get(
        "VAPID_PUBLIC_KEY"
    )


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

            }

        )

        return True


    except WebPushException as e:

        print(
            f"Push notification failed: {e}"
        )


        status_code = None


        if e.response is not None:

            status_code = e.response.status_code

            print(
                f"Push response status: {status_code}"
            )

            try:

                print(
                    f"Response body: {e.response.text}"
                )

            except Exception:

                pass


        # --------------------------------
        # Remove invalid subscriptions
        # --------------------------------

        if status_code in [400, 404, 410]:

            try:

                db.session.delete(
                    subscription
                )

                db.session.commit()

                print(
                    "Invalid push subscription removed."
                )

            except Exception as delete_error:

                db.session.rollback()

                print(
                    f"Failed to remove push subscription: "
                    f"{delete_error}"
                )


        return False


    except Exception as e:

        print(
            f"Unexpected push notification error: {e}"
        )

        return False
