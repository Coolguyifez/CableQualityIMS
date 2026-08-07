from flask import (
    Blueprint,
    render_template,
    redirect,
    url_for,
    flash,
    request
)

from flask_login import (
    login_user,
    logout_user,
    current_user,
    login_required
)

from .extensions import db

from .models import (
    Company,
    User
)

from .forms import (
    LoginForm,
    CompanyRegistrationForm
)

auth = Blueprint(
    "auth",
    __name__,
    template_folder="templates"
)


# -----------------------------------
# Helper Function
# -----------------------------------

def get_company(company_name):

    return Company.query.filter(

        Company.company_name.ilike(
            company_name.strip()
        )

    ).first()


# -----------------------------------
# Home Redirect
# -----------------------------------

@auth.route("/")

def index():

    if current_user.is_authenticated:

        return redirect(
            url_for("main.dashboard")
        )

    return redirect(
        url_for("auth.login")
    )

# -----------------------------------
# Company Registration
# -----------------------------------

@auth.route(
    "/register-company",
    methods=["GET", "POST"]
)
def register_company():

    if current_user.is_authenticated:

        return redirect(
            url_for("main.home")
        )

    form = CompanyRegistrationForm()

    if form.validate_on_submit():

        company = Company.query.filter_by(

            company_name=form.company_name.data.strip()

        ).first()

        if company:

            flash(

                "Company already exists.",

                "danger"

            )

            return render_template(

                "auth/register_company.html",

                form=form

            )

        company_code = Company.query.filter_by(

            company_code=form.company_code.data.strip()

        ).first()

        if company_code:

            flash(

                "Company code already exists.",

                "danger"

            )

            return render_template(

                "auth/register_company.html",

                form=form

            )

        new_company = Company(

            company_name=form.company_name.data.strip(),

            company_code=form.company_code.data.strip(),

            address=form.company_address.data,

            email=form.company_email.data,

            phone=form.company_phone.data

        )

        db.session.add(

            new_company

        )

        db.session.flush()

        username_exists = User.query.filter_by(

            company_id=new_company.id,

            username=form.username.data.strip()

        ).first()

        if username_exists:

            flash(

                "Username already exists in this company.",

                "danger"

            )

            db.session.rollback()

            return render_template(

                "auth/register_company.html",

                form=form

            )

        email_exists = User.query.filter_by(

            company_id=new_company.id,

            email=form.email.data.strip()

        ).first()

        if email_exists:

            flash(

                "Email already exists in this company.",

                "danger"

            )

            db.session.rollback()

            return render_template(

                "auth/register_company.html",

                form=form

            )

        admin = User(

            company_id=new_company.id,

            full_name=form.admin_name.data,

            username=form.username.data,

            email=form.email.data,

            role="Company Administrator"

        )

        admin.set_password(

            form.password.data

        )

        db.session.add(

            admin

        )

        db.session.commit()

        login_user(

            admin

        )

        flash(

            "Company created successfully.",

            "success"

        )

        return redirect(

            url_for("main.home")

        )

    return render_template(

        "auth/register_company.html",

        form=form

    )

# -----------------------------------
# Login
# -----------------------------------

@auth.route(
    "/login",
    methods=["GET", "POST"]
)
def login():

    if current_user.is_authenticated:

        return redirect(
            url_for("main.home")
        )

    form = LoginForm()

    if form.validate_on_submit():

        company = Company.query.filter(
            Company.company_name.ilike(
                form.company.data.strip()
            )
        ).first()

        if not company:

            flash(
                "Company not found.",
                "danger"
            )

            return render_template(
                "auth/login.html",
                form=form
            )

        if not company.is_active:

            flash(
                "This company account has been deactivated.",
                "danger"
            )

            return render_template(
                "auth/login.html",
                form=form
            )

        user = User.query.filter_by(
            company_id=company.id,
            username=form.username.data.strip()
        ).first()

        if not user:

            flash(
                "Invalid username or password.",
                "danger"
            )

            return render_template(
                "auth/login.html",
                form=form
            )

        if not user.is_active:

            flash(
                "Your account has been disabled.",
                "danger"
            )

            return render_template(
                "auth/login.html",
                form=form
            )

        if not user.check_password(
            form.password.data
        ):

            flash(
                "Invalid username or password.",
                "danger"
            )

            return render_template(
                "auth/login.html",
                form=form
            )

        login_user(
            user,
            remember=form.remember.data
        )

        next_page = request.args.get("next")

        flash(
            f"Welcome, {user.full_name}.",
            "success"
        )

        if next_page:

            return redirect(next_page)

        return redirect(
            url_for("main.home")
        )

    return render_template(
        "auth/login.html",
        form=form
    )

# -----------------------------------
# Logout
# -----------------------------------

@auth.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have successfully logged out.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )