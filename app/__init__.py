from flask import Flask
import time
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
    # Automatic CAPA / Production Line Check
    # --------------------------------

    last_capa_check = [0]
    CAPA_CHECK_INTERVAL = 60  # seconds

    @app.before_request
    def automatic_capa_check():

        current_time = time.time()

        # Prevent checking the database on every request.
        if current_time - last_capa_check[0] < CAPA_CHECK_INTERVAL:
            return

        last_capa_check[0] = current_time

        try:
            from .models import CAPA
            from .routes import update_capa_status

            capas = CAPA.query.all()

            changed = False

            for capa in capas:

                if update_capa_status(capa):
                    changed = True

                    app.logger.info(
                        "Automatic CAPA check: "
                        "CAPA %s updated. Status: %s",
                        capa.id,
                        capa.status
                    )

            if changed:
                db.session.commit()

        except Exception:
            db.session.rollback()

            app.logger.exception(
                "Automatic CAPA status check failed."
            )

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

    # error message handler
    @app.errorhandler(500)
    def internal_server_error(error):
        db.session.rollback()

        return render_template(
            "errors/500.html"
        ), 500

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template(
            "errors/404.html"
        ), 404


    return app

