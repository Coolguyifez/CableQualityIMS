from functools import wraps

from flask import (
    flash,
    redirect,
    url_for
)

from flask_login import (
    current_user,
    login_required
)

from .permissions import ROLE_PERMISSIONS


# ======================================================
# SYSTEM ADMINISTRATOR
# ======================================================

def system_admin_required(f):

    @wraps(f)

    @login_required
    def decorated_function(*args, **kwargs):

        if current_user.role != "System Administrator":

            flash(
                "Access denied.",
                "danger"
            )

            return redirect(
                url_for("main.home")
            )

        return f(*args, **kwargs)

    return decorated_function


# ======================================================
# COMPANY ADMINISTRATOR
# ======================================================

def company_admin_required(f):

    @wraps(f)

    @login_required
    def decorated_function(*args, **kwargs):

        if current_user.role not in [

            "System Administrator",

            "Company Administrator"

        ]:

            flash(
                "Access denied.",
                "danger"
            )

            return redirect(
                url_for("main.home")
            )

        return f(*args, **kwargs)

    return decorated_function


# ======================================================
# ROLES REQUIRED
# ======================================================

def roles_required(*roles):

    def decorator(f):

        @wraps(f)

        @login_required
        def decorated_function(*args, **kwargs):

            if current_user.role not in roles:

                flash(
                    "You do not have permission to access this page.",
                    "danger"
                )

                return redirect(
                    url_for("main.home")
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


# ======================================================
# PERMISSION REQUIRED
# ======================================================

def permission_required(permission):

    def decorator(f):

        @wraps(f)

        @login_required
        def decorated_function(*args, **kwargs):

            permissions = ROLE_PERMISSIONS.get(

                current_user.role,

                set()

            )

            if permission not in permissions:

                flash(
                    "You do not have permission to perform this action.",
                    "danger"
                )

                return redirect(
                    url_for("main.home")
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator