from flask import Flask
from config import Config

from .extensions import (
    db,
    login_manager,
    bcrypt,
    migrate
)

from flask_login import current_user
from .models import User, Notification


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    # --------------------------------
    # Initialize extensions
    # --------------------------------

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    migrate.init_app(app, db)

    # --------------------------------
    # Login settings
    # --------------------------------

    login_manager.login_view = "auth.login"

    login_manager.login_message = (
        "Please log in to continue."
    )

    login_manager.login_message_category = "warning"

    # --------------------------------
    # Register blueprints
    # --------------------------------

    from .routes import main
    from .auth import auth

    app.register_blueprint(main)
    app.register_blueprint(auth)

    # --------------------------------
    # Notifications
    # --------------------------------

    @app.context_processor
    def inject_notifications():

        unread_notifications = 0
        latest_notifications = []

        if current_user.is_authenticated:

            unread_notifications = (
                Notification.query
                .filter_by(
                    company_id=current_user.company_id,
                    user_id=current_user.id,
                    is_read=False
                )
                .count()
            )

            latest_notifications = (
                Notification.query
                .filter_by(
                    company_id=current_user.company_id,
                    user_id=current_user.id
                )
                .order_by(
                    Notification.created_at.desc()
                )
                .limit(5)
                .all()
            )

        return {
            "unread_notifications": unread_notifications,
            "latest_notifications": latest_notifications
        }

    return app

