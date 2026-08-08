from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from .forms import CustomerForm, CableTypeForm, ProductionLineForm, CableBatchForm, InspectionForm, QualityMetricForm,  QualitySpecificationForm, DeviationForm, CAPAForm, CompanyForm, ThemeSettingsForm, AccountSettingsForm, NotificationSettingsForm
from .models import Customer, User, CableType, ProductionLine, CableBatch, Inspection, QualityMetric, QualitySpecification, Deviation, CAPA, Notification, Company, AuditLog
from .extensions import db, bcrypt
from datetime import datetime
from datetime import date
from .audit import log_activity
from .utils import create_notification
from sqlalchemy.exc import IntegrityError
from app.report_utils import (
    get_filtered_inspection_query,
    get_filtered_deviation_query,
    get_filtered_capa_query,
    get_filtered_quality_metric_query,
    get_filtered_production_query,
    get_filtered_customer_query,
    get_filtered_user_query,
    get_filtered_audit_query,
    apply_deviation_sort,
    apply_inspection_sort,
    apply_capa_sort,
    apply_quality_metric_sort,
    apply_production_sort,
    apply_customer_sort,
    apply_user_sort,
    apply_audit_sort,
    paginate_query,
    get_inspection_statistics,
    get_capa_statistics,
    get_quality_metric_statistics,
    get_production_statistics,
    get_customer_statistics,
    get_user_statistics,
    get_audit_statistics,
    get_audit_chart,
    get_quality_metric_chart,
    get_capa_effectiveness_chart,
    get_production_status_chart,
    get_result_chart_data,
    get_capa_status_chart,
    get_user_status_chart,
    get_monthly_trend,
    get_production_line_chart,
    get_customer_request_chart,
    get_cable_type_chart,
    get_deviation_statistics,
    get_deviation_chart,
    get_severity_chart,
    export_excel,
    export_pdf,
    build_rows
)
from .dashboard_utils import (

    get_dashboard_statistics,

    inspection_chart,

    monthly_inspection_chart,

    capa_chart,

    deviation_chart,

    production_line_chart,

    recent_inspections,

    recent_capas,

    recent_audits,

    pass_rate,

    overdue_capas,

    todays_activities

)

from flask_login import (
    login_user,
    logout_user,
    login_required,
    current_user
)
from werkzeug.security import generate_password_hash

from app.forms import (
    LoginForm,
    UserForm,
    ChangePasswordForm
)

from app.models import User
from .decorators import (
    system_admin_required,
    company_admin_required,
    permission_required,
    roles_required
)




main = Blueprint("main", __name__)

def generate_batch_number(production_date):

    prefix = production_date.strftime(

        "CB-%Y%m%d"

    )

    last_batch = (

        CableBatch.query.filter(

            CableBatch.batch_number.like(

                f"{prefix}%"

            )

        )

        .order_by(

            CableBatch.id.desc()

        )

        .first()

    )

    if last_batch:

        last = int(

            last_batch.batch_number.split("-")[-1]

        )

        sequence = last + 1

    else:

        sequence = 1

    return f"{prefix}-{sequence:03d}"

def generate_cable_construction(cable_type):
    """
    Automatically builds the cable construction.
    Example:
    2P X 4.0mm CU(SOL)/XLPE/MICA/LSZH/SWA/PVC - FR
    """

    return (
        f"{cable_type.pair_count} X {cable_type.conductor_size} "
        f"{cable_type.conductor_material}/"
        f"{cable_type.insulation_material}/"
        f"{cable_type.fire_resistant_material}/"
        f"{cable_type.inner_sheath_material}/"
        f"{cable_type.armour_type}/"
        f"{cable_type.outer_sheath_material}"
        f" - {cable_type.flame_retardant}"
    )

def generate_cable_code(
        cable_type,
        drain_wire_type,
        specialty,
        water_barrier,
        outer_colour
):
    """
    Example:

    P-A-05-R-N-C-BK
    """

    SIZE_CODES = {
        "1.0mm": "C",
        "1.5mm": "D",
        "2.5mm": "E",
        "4.0mm": "F"
    }

    PAIR_CODES = {
        "1P": "01",
        "2P": "02",
        "5P": "05",
        "8P": "08",
        "10P": "10",
        "20P": "20"
    }

    pair = PAIR_CODES.get(
        cable_type.pair_count,
        "00"
    )

    size = SIZE_CODES.get(
        cable_type.conductor_size,
        "X"
    )

    armour = (
        "P"
        if cable_type.armour_type == "SWA"
        else "N"
    )

    return (
        f"{drain_wire_type}-"
        f"{specialty}-"
        f"{pair}-"
        f"{water_barrier}-"
        f"{armour}-"
        f"{size}-"
        f"{outer_colour}"
    )


from datetime import date
from app.models import Inspection

def generate_inspection_number(inspection_date):
    """
    Example:
    INSP-20260725-001
    """

    prefix = inspection_date.strftime("%Y%m%d")

    count = Inspection.query.filter(
        Inspection.inspection_date == inspection_date
    ).count()

    sequence = count + 1

    return f"INSP-{prefix}-{sequence:03d}"


def validate_result(specification, measured_value):
    """
    Validates a measured value against a QualitySpecification.

    Returns:
        (passed, result)

        passed -> True/False
        result -> "Pass" or "Fail"
    """

    validation = specification.validation_type

    try:

        # Accept Any Value
        if validation == "any":
            return True, "Pass"

        # Minimum
        elif validation == "minimum":

            value = float(measured_value)

            return (
                value >= specification.minimum_value,
                "Pass" if value >= specification.minimum_value else "Fail"
            )

        # Maximum
        elif validation == "maximum":

            value = float(measured_value)

            return (
                value <= specification.maximum_value,
                "Pass" if value <= specification.maximum_value else "Fail"
            )

        # Range
        elif validation == "range":

            value = float(measured_value)

            passed = (
                specification.minimum_value
                <= value
                <= specification.maximum_value
            )

            return (
                passed,
                "Pass" if passed else "Fail"
            )

        # Text comparison
        elif validation == "text":

            expected = {
                colour.strip().upper()
                for colour in (specification.expected_result or "").split(",")
                if colour.strip()
            }

            measured = {
                colour.strip().upper()
                for colour in str(measured_value).split(",")
                if colour.strip()
            }

            passed = expected == measured

            return (
                passed,
                "Pass" if passed else "Fail"
            )

    except (ValueError, TypeError):

        return False, "Fail"

    return False, "Fail"


def update_inspection_status(inspection_id):

    inspection = Inspection.query.get_or_404(inspection_id)

    metrics = QualityMetric.query.filter_by(
        inspection_id=inspection.id
    ).all()

    total_specs = QualitySpecification.query.filter_by(
        cable_type_id=inspection.batch.cable_type_id
    ).count()

    if len(metrics) == 0:

        inspection.overall_result = "Pending"

    elif len(metrics) < total_specs:

        inspection.overall_result = "Pending"

    elif any(metric.result == "Fail" for metric in metrics):

        inspection.overall_result = "Fail"

    else:

        inspection.overall_result = "Pass"

    db.session.commit()

def generate_deviation_number():

    today = datetime.now().strftime("%Y-%m%d")

    last = (
        Deviation.query
        .order_by(Deviation.id.desc())
        .first()
    )

    if last:

        last_number = int(last.deviation_number.split("-")[-1])

        next_number = last_number + 1

    else:

        next_number = 1

    return f"DEV:{today}-{next_number:03d}"



def get_capa_status(capa):
    """
    Returns the current status of a CAPA.
    """

    if capa.status == "Closed":
        return "Closed"

    if (
        capa.due_date
        and date.today() > capa.due_date
    ):
        return "Overdue"

    return capa.status

def get_days_overdue(capa):

    if (
        capa.due_date
        and
        date.today() > capa.due_date
        and
        capa.status != "Closed"
    ):

        return (
            date.today() - capa.due_date
        ).days

    return 0

def update_capa_status(capa):

    if capa.status == "Closed":
        return

    if (
        capa.due_date
        and date.today() > capa.due_date
        and capa.status != "Overdue"
    ):

        capa.status = "Overdue"

@main.route("/")
@login_required
def home():

    company_id = current_user.company_id

    stats = get_dashboard_statistics(

        company_id

    )

    return render_template(

        "dashboard.html",

        stats=stats,

        inspection_chart=inspection_chart(

            company_id

        ),

        monthly_chart=monthly_inspection_chart(

            company_id

        ),

        capa_chart=capa_chart(

            company_id

        ),

        deviation_chart=deviation_chart(

            company_id

        ),

        production_chart=production_line_chart(

            company_id

        ),

        pass_rate=pass_rate(

            company_id

        ),

        overdue_capas=overdue_capas(

            company_id

        ),

        todays_activities=todays_activities(

            company_id

        ),

        recent_inspections=recent_inspections(

            company_id

        ),

        recent_capas=recent_capas(

            company_id

        ),

        recent_audits=recent_audits(

            company_id

        )

    )


@main.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(
            url_for("main.home")
        )

    form = LoginForm()

    if form.validate_on_submit():

        company = Company.query.filter_by(
            company_code=form.company_code.data.upper()
        ).first()

        if not company:

            flash(
                "Invalid company code.",
                "danger"
            )

            return render_template(
                "auth/login.html",
                form=form
            )

        user = User.query.filter_by(
            company_id=company.id,
            username=form.username.data
        ).first()

        if (
            user
            and user.check_password(form.password.data)
            and user.is_active
        ):

            login_user(
                user,
                remember=form.remember.data
            )

            flash(
                f"Welcome to {company.company_name}.",
                "success"
            )

            return redirect(
                url_for("main.home")
            )

        flash(
            "Invalid username or password.",
            "danger"
        )

    return render_template(
        "auth/login.html",
        form=form
    )

@main.route("/logout")
@login_required
def logout():

    logout_user()

    flash(
        "You have been logged out.",
        "info"
    )

    return redirect(
        url_for("main.login")
    )

@main.route("/users")
@login_required
@roles_required("Company Administrator")
def users():

    users = User.query.filter_by(

        company_id=current_user.company_id

    ).order_by(

        User.full_name

    ).all()

    return render_template(

        "users.html",

        users=users

    )

@main.route(
    "/users/new",
    methods=["GET", "POST"]
)
@login_required
@roles_required("Company Administrator")
def new_user():

    form = UserForm()

    if form.validate_on_submit():

        username_exists = User.query.filter_by(

            company_id=current_user.company_id,

            username=form.username.data

        ).first()

        if username_exists:

            flash(

                "Username already exists.",

                "danger"

            )

            return render_template(

                "user_form.html",

                form=form,

                title="New User"

            )

        email_exists = User.query.filter_by(

            company_id=current_user.company_id,

            email=form.email.data

        ).first()

        if email_exists:

            flash(

                "Email already exists.",

                "danger"

            )

            return render_template(

                "user_form.html",

                form=form,

                title="New User"

            )

        user = User(

            company_id=current_user.company_id,

            full_name=form.full_name.data,

            username=form.username.data,

            email=form.email.data,

            role=form.role.data,

            is_active=form.is_active.data

        )

        if form.password.data:

            user.set_password(

                form.password.data

            )

        db.session.add(

            user

        )

        log_activity(

            module="User",

            action="Create",

            description=(
                f"{current_user.full_name} created user "
                f"'{user.username}' "
                f"({user.role})"
            )

        )

        db.session.commit()

        flash(

            "User created successfully.",

            "success"

        )

        return redirect(

            url_for("main.users")

        )

    return render_template(

        "user_form.html",

        form=form,

        title="New User"

    )

@main.route(
    "/users/<int:user_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@roles_required("Company Administrator")
def edit_user(user_id):

    user = User.query.filter_by(

        id=user_id,

        company_id=current_user.company_id

    ).first_or_404()

    form = UserForm(obj=user)

    if form.validate_on_submit():

        username_exists = User.query.filter(

            User.company_id == current_user.company_id,

            User.username == form.username.data,

            User.id != user.id

        ).first()

        if username_exists:

            flash(

                "Username already exists.",

                "danger"

            )

            return render_template(

                "user_form.html",

                form=form,

                title="Edit User"

            )

        email_exists = User.query.filter(

            User.company_id == current_user.company_id,

            User.email == form.email.data,

            User.id != user.id

        ).first()

        if email_exists:

            flash(

                "Email already exists.",

                "danger"

            )

            return render_template(

                "user_form.html",

                form=form,

                title="Edit User"

            )

        user.full_name = form.full_name.data

        user.username = form.username.data

        user.email = form.email.data

        user.role = form.role.data

        user.is_active = form.is_active.data

        if form.password.data:

            user.set_password(

                form.password.data

            )

        log_activity(

            module="User",

            action="Update",

            description=(
                f"{current_user.full_name} updated user "
                f"'{user.username}'"
            )
        )

        db.session.commit()

        flash(

            "User updated successfully.",

            "success"

        )

        return redirect(

            url_for("main.users")

        )

    return render_template(

        "user_form.html",

        form=form,

        title="Edit User"

    )


@main.route("/users/<int:user_id>/delete")
@login_required
@roles_required("Company Administrator")
def delete_user(user_id):

    user = User.query.filter_by(

        id=user_id,

        company_id=current_user.company_id

    ).first_or_404()

    if user.id == current_user.id:

        flash(

            "You cannot delete your own account.",

            "danger"

        )

        return redirect(

            url_for("main.users")

        )

    log_activity(

        module="User",

        action="Delete",

        description=(
            f"{current_user.full_name} deleted user "
            f"'{user.username}'"
        )

    )

    db.session.delete(user)

    db.session.commit()

    flash(

        "User deleted successfully.",

        "success"

    )

    return redirect(

        url_for("main.users")

    )


@main.route("/companies")

@login_required

@system_admin_required

def companies():

    companies = Company.query.order_by(

        Company.company_name

    ).all()

    return render_template(

        "companies.html",

        companies=companies

    )

@main.route(

    "/companies/new",

    methods=["GET","POST"]

)

@login_required

@system_admin_required

def new_company():

    form = CompanyForm()

    if form.validate_on_submit():

        company = Company(

            company_name=form.company_name.data,

            company_code=form.company_code.data.upper(),

            address=form.address.data,

            email=form.email.data,

            phone=form.phone.data,

            logo=form.logo.data,

            is_active=form.is_active.data

        )

        db.session.add(company)
        log_activity(

            module="Company",

            action="Create",

            description=f"Created company '{company.company_name}'"

        )

        db.session.commit()

        flash(

            "Company created successfully.",

            "success"

        )

        admin = User(

            company_id=company.id,

            full_name=form.admin_full_name.data,

            username=form.admin_username.data,

            email=form.admin_email.data,

            role="Company Administrator",

            is_active=True

        )

        admin.set_password(

            form.admin_password.data

        )

        db.session.add(admin)

        db.session.commit()

        return redirect(

            url_for("main.companies")

        )

    return render_template(

        "company_form.html",

        form=form,

        title="New Company"

    )

@main.route(

    "/companies/<int:company_id>/edit",

    methods=["GET","POST"]

)

@login_required

@system_admin_required

def edit_company(company_id):

    company = Company.query.get_or_404(

        company_id

    )

    form = CompanyForm(

        obj=company

    )

    if form.validate_on_submit():

        form.populate_obj(company)

        log_activity(

            module="Company",

            action="Update",

            description=f"Updated company '{company.company_name}'"

        )

        db.session.commit()

        flash(

            "Company updated successfully.",

            "success"

        )

        return redirect(

            url_for("main.companies")

        )

    return render_template(

        "company_form.html",

        form=form,

        title="Edit Company"

    )

@main.route("/companies/<int:company_id>/toggle")
@login_required
@system_admin_required
def toggle_company(company_id):

    company = Company.query.get_or_404(
        company_id
    )

    company.is_active = not company.is_active

    if company.is_active:

        log_activity(

            module="Company",

            action="Enable",

            description=(
                f"{current_user.full_name} enabled "
                f"company '{company.company_name}'"
                f"({company.company_code})"
            )

        )

        message = "Company enabled successfully."

    else:

        log_activity(

            module="Company",

            action="Disable",

            description=(
                f"{current_user.full_name} disabled "
                f"company '{company.company_name}'"
                f"({company.company_code})"
            )

        )

        message = "Company disabled successfully."

    db.session.commit()

    flash(
        message,
        "success"
    )

    return redirect(
        url_for("main.companies")
    )

@main.route("/profile")
@login_required
def profile():

    return render_template(
        "profile.html",
        user=current_user,
        company=current_user.company
    )




@main.route("/customers")
@login_required
@permission_required("manage_customers")
def customers():

    customers = Customer.query.filter_by(
        company_id=current_user.company_id
    ).order_by(
        Customer.company_name
    ).all()

    return render_template(
        "customers.html",
        customers=customers
    )

@main.route("/customers/new", methods=["GET", "POST"])
@permission_required("manage_customers")
@login_required
def new_customer():

    form = CustomerForm()

    if form.validate_on_submit():

        customer = Customer(
            company_id=current_user.company_id,
            company_name=form.company_name.data,
            contact_person=form.contact_person.data,
            email=form.email.data,
            phone=form.phone.data,
            address=form.address.data
        )

        db.session.add(customer)

        log_activity(

            module="Customer",

            action="Create",

            description=f"Created customer '{customer.company_name}'"

        )

        db.session.commit()

        flash(
            "Customer added successfully.",
            "success"
        )

        return redirect(
            url_for("main.customers")
        )

    return render_template(
        "customer_form.html",
        form=form
    )

@main.route("/customers/<int:customer_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("manage_customers")
def edit_customer(customer_id):
    customer = Customer.query.filter_by(
        id=customer_id,
        company_id=current_user.company_id
    ).first_or_404()

    form = CustomerForm(obj=customer)

    if form.validate_on_submit():

        customer.company_name = form.company_name.data
        customer.contact_person = form.contact_person.data
        customer.email = form.email.data
        customer.phone = form.phone.data
        customer.address = form.address.data


        log_activity(

            module="Customer",

            action="Update",

            description=f"Updated customer '{customer.company_name}'"

        )

        db.session.commit()

        flash(
            "Customer updated successfully.",
            "success"
        )

        return redirect(url_for("main.customers"))

    return render_template(
        "customer_form.html",
        form=form
    )


@main.route("/customers/<int:customer_id>/delete")
@login_required
@permission_required("manage_customers")
def delete_customer(customer_id):
    customer = Customer.query.filter_by(
        id=customer_id,
        company_id=current_user.company_id
    ).first_or_404()

    log_activity(

        module="Customer",

        action="Delete",

        description=f"Deleted customer '{customer.company_name}'"

    )
    db.session.delete(customer)

    db.session.commit()

    flash(
        "Customer deleted successfully.",
        "success"
    )

    return redirect(
        url_for("main.customers")
    )

# ==========================
# CABLE TYPES
# ==========================

@main.route("/cable-types")
@permission_required("manage_cable_types")
@login_required
def cable_types():
    cable_types = CableType.query.filter_by(
        company_id=current_user.company_id
    ).order_by(
        CableType.name
    ).all()

    return render_template(
        "cable_types.html",
        cable_types=cable_types
    )


@main.route("/cable-types/new", methods=["GET", "POST"])
@login_required
@permission_required("manage_cable_types")
def new_cable_type():

    form = CableTypeForm()

    if form.validate_on_submit():

        construction = "/".join(
            filter(None, [
                form.conductor_material.data,
                form.insulation_material.data,
                None if form.fire_resistant_material.data == "NONE" else form.fire_resistant_material.data,
                form.inner_sheath_material.data,
                form.armour_type.data,
                form.outer_sheath_material.data,
            ])
        )

        if form.flame_retardant.data != "NONE":
            construction += f" - {form.flame_retardant.data}"

        existing = CableType.query.filter_by(
            company_id=current_user.company_id,
            name=construction
        ).first()

        if existing:

            flash(
                "Cable Type already exists.",
                "warning"
            )

            return render_template(
                "cable_type_form.html",
                form=form
            )

        cable = CableType(

            company_id=current_user.company_id,

            name=construction,

            pair_count=form.pair_count.data,

            conductor_size=form.conductor_size.data,

            voltage_rating=form.voltage_rating.data,

            drain_configuration=form.drain_configuration.data,

            conductor_material=form.conductor_material.data,

            insulation_material=form.insulation_material.data,

            fire_resistant_material=form.fire_resistant_material.data,

            inner_sheath_material=form.inner_sheath_material.data,

            armour_type=form.armour_type.data,

            outer_sheath_material=form.outer_sheath_material.data,

            flame_retardant=form.flame_retardant.data,

            application=form.application.data
        )

        db.session.add(cable)

        log_activity(

            module="Cable Type",

            action="Create",

            description=f"Created cable type '{cable.name}'"

        )

        db.session.commit()

        flash(
            "Cable Type added successfully.",
            "success"
        )

        return redirect(url_for("main.cable_types"))

    return render_template(
        "cable_type_form.html",
        form=form
    )


@main.route("/cable-types/<int:id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("manage_cable_types")
def edit_cable_type(id):

    cable = CableType.query.filter_by(
        id=id,
        company_id=current_user.company_id
    ).first_or_404()

    form = CableTypeForm(obj=cable)

    if form.validate_on_submit():

        # Update all fields except the generated name
        form.populate_obj(cable)

        # Generate Construction Name automatically
        construction = "/".join(
            filter(None, [
                form.conductor_material.data,
                form.insulation_material.data,
                None if form.fire_resistant_material.data == "NONE"
                else form.fire_resistant_material.data,
                form.inner_sheath_material.data,
                form.armour_type.data,
                form.outer_sheath_material.data,
            ])
        )

        # Add Flame Retardant if selected
        if form.flame_retardant.data != "NONE":
            construction += f" - {form.flame_retardant.data}"

        # Save generated construction as the cable name
        cable.name = construction

        db.session.commit()

        log_activity(
            module="Cable Type",
            action="Update",
            description=f"Updated cable type '{cable.name}'"
        )

        flash(
            "Cable Type updated successfully.",
            "success"
        )

        return redirect(url_for("main.cable_types"))

    return render_template(
        "cable_type_form.html",
        form=form
    )


@main.route("/cable-types/<int:id>/delete")
@login_required
@permission_required("manage_cable_types")
def delete_cable_type(id):

    cable = CableType.query.filter_by(
        id=id,
        company_id=current_user.company_id
    ).first_or_404()


    log_activity(

        module="Cable Type",

        action="Delete",

        description=f"Deleted cable type '{cable.name}'"

    )

    db.session.delete(cable)

    db.session.commit()

    flash(
        "Cable Type deleted.",
        "success"
    )

    return redirect(url_for("main.cable_types"))


# ==========================================
# PRODUCTION LINES
# ==========================================

@main.route("/production-lines")
@permission_required("manage_production_lines")
@login_required
def production_lines():
    production_lines = ProductionLine.query.filter_by(
        company_id=current_user.company_id
    ).order_by(
        ProductionLine.line_name
    ).all()

    return render_template(
        "production_lines.html",
        production_lines=production_lines
    )


@main.route("/production-lines/new", methods=["GET", "POST"])
@login_required
@permission_required("manage_production_lines")
def new_production_line():

    form = ProductionLineForm()

    if form.validate_on_submit():

        line = ProductionLine(

            company_id=current_user.company_id,

            line_name=form.line_name.data,

            location=form.location.data,

            supervisor=form.supervisor.data,

            status=form.status.data

        )

        db.session.add(line)

        log_activity(

            module="Production Line",

            action="Create",

            description=f"Created production line '{line.line_name}'"

        )

        db.session.commit()

        flash(
            "Production Line created successfully.",
            "success"
        )

        return redirect(
            url_for("main.production_lines")
        )

    return render_template(
        "production_line_form.html",
        form=form
    )


@main.route("/production-lines/<int:id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("manage_production_lines")
def edit_production_line(id):

    line = ProductionLine.query.filter_by(
        id=id,
        company_id=current_user.company_id
    ).first_or_404()

    form = ProductionLineForm(obj=line)

    if form.validate_on_submit():

        form.populate_obj(line)

        log_activity(

            module="Production Line",

            action="Update",

            description=f"Updated production line '{line.line_name}'"

        )

        db.session.commit()

        flash(
            "Production Line updated.",
            "success"
        )

        return redirect(
            url_for("main.production_lines")
        )

    return render_template(
        "production_line_form.html",
        form=form
    )


@main.route("/production-lines/<int:id>/delete")
@login_required
@permission_required("manage_production_lines")
def delete_production_line(id):
    line = ProductionLine.query.filter_by(
        id=id,
        company_id=current_user.company_id
    ).first_or_404()


    log_activity(

        module="Production Line",

        action="Delete",

        description=f"Deleted production line '{line.line_name}'"

    )

    db.session.delete(line)

    db.session.commit()

    flash(
        "Production Line deleted.",
        "success"
    )

    return redirect(
        url_for("main.production_lines")
    )

# =====================================
# CABLE BATCHES
# =====================================

@main.route("/batches")
@permission_required("manage_batches")
@login_required
def batches():

    batches = CableBatch.query.filter_by(
        company_id=current_user.company_id
    ).order_by(
        CableBatch.production_date.desc()
    ).all()

    return render_template(
        "batches.html",
        batches=batches
    )


@main.route("/batches/new", methods=["GET", "POST"])
@login_required
@permission_required("manage_batches")
def new_batch():

    form = CableBatchForm()

    customers = Customer.query.filter_by(
        company_id=current_user.company_id
    ).order_by(
        Customer.company_name
    ).all()

    cable_types = CableType.query.filter_by(
        company_id=current_user.company_id
    ).order_by(
        CableType.name
    ).all()

    production_lines = ProductionLine.query.filter_by(
        company_id=current_user.company_id
    ).order_by(
        ProductionLine.line_name
    ).all()

    form.customer_id.choices = [
        (c.id, c.company_name)
        for c in customers
    ]

    form.cable_type_id.choices = [
        (c.id, c.name)
        for c in cable_types
    ]

    form.production_line_id.choices = [
        (p.id, p.line_name)
        for p in production_lines
    ]

    if form.validate_on_submit():

        batch = CableBatch(

            company_id=current_user.company_id,

            batch_number=generate_batch_number(
                form.production_date.data
            ),

            drum_number=form.drum_number.data.strip(),

            customer_id=form.customer_id.data,

            cable_type_id=form.cable_type_id.data,

            production_line_id=form.production_line_id.data,

            production_date=form.production_date.data,

            cable_length=form.cable_length.data,

            status=form.status.data,

            drain_wire_type=form.drain_wire_type.data,

            specialty=form.specialty.data,

            water_barrier=form.water_barrier.data,

            outer_sheath_colour=form.outer_sheath_colour.data,

            cable_code = form.cable_code.data

        )

        try:

            db.session.add(batch)

            log_activity(

                module="Cable Batch",

                action="Create",

                description=f"Created batch '{batch.batch_number}'"

            )

            db.session.commit()

            flash(
                "Cable Batch created successfully.",
                "success"
            )

            return redirect(
                url_for("main.batches")
            )



        except IntegrityError:

            db.session.rollback()

            flash(

                "Unable to create batch. Please try again.",

                "danger"

            )
    return render_template(

        "batch_form.html",

        form=form,

        cable_types=cable_types,

        title="New Cable Batch"

    )


@main.route(
    "/batches/<int:batch_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@permission_required("manage_batches")
def edit_batch(batch_id):

    batch = CableBatch.query.filter_by(

        id=batch_id,

        company_id=current_user.company_id

    ).first_or_404()

    form = CableBatchForm(obj=batch)

    customers = Customer.query.filter_by(
        company_id=current_user.company_id
    ).order_by(
        Customer.company_name
    ).all()

    cable_types = CableType.query.filter_by(
        company_id=current_user.company_id
    ).order_by(
        CableType.name
    ).all()

    production_lines = ProductionLine.query.filter_by(
        company_id=current_user.company_id
    ).order_by(
        ProductionLine.line_name
    ).all()

    form.customer_id.choices = [
        (c.id, c.company_name)
        for c in customers
    ]

    form.cable_type_id.choices = [
        (c.id, c.name)
        for c in cable_types
    ]

    form.production_line_id.choices = [
        (p.id, p.line_name)
        for p in production_lines
    ]

    if form.validate_on_submit():

        batch.drum_number = form.drum_number.data.strip()

        batch.customer_id = form.customer_id.data

        batch.cable_type_id = form.cable_type_id.data

        batch.production_line_id = form.production_line_id.data

        batch.production_date = form.production_date.data

        batch.cable_length = form.cable_length.data

        batch.status = form.status.data

        batch.drain_wire_type = form.drain_wire_type.data

        batch.specialty = form.specialty.data

        batch.water_barrier = form.water_barrier.data

        batch.outer_sheath_colour = form.outer_sheath_colour.data

        batch.cable_code = form.cable_code.data

        log_activity(

            module="Cable Batch",

            action="Update",

            description=f"Updated batch '{batch.batch_number}'"

        )

        db.session.commit()

        flash(
            "Batch updated successfully.",
            "success"
        )

        return redirect(
            url_for("main.batches")
        )

    return render_template(

        "batch_form.html",

        form=form,

        cable_types=cable_types,

        title="Edit Cable Batch"

    )


@main.route(
    "/batches/<int:batch_id>/delete"
)
@login_required
@permission_required("manage_batches")
def delete_batch(batch_id):

    batch = CableBatch.query.filter_by(
        id=batch_id,
        company_id=current_user.company_id
    ).first_or_404()


    log_activity(

        module="Cable Batch",

        action="Delete",

        description=f"Deleted batch '{batch.batch_number}'"

    )

    db.session.delete(batch)

    db.session.commit()

    flash(
        "Batch deleted successfully.",
        "success"
    )

    return redirect(
        url_for("main.batches")
    )


# ===========================================
# INSPECTIONS
# ===========================================

@main.route("/inspections")
@permission_required("manage_inspections")
@login_required
def inspections():

    inspections = Inspection.query.filter_by(
        company_id=current_user.company_id
    ).order_by(
        Inspection.inspection_date.desc()
    ).all()

    return render_template(
        "inspections.html",
        inspections=inspections
    )


@main.route("/inspections/new", methods=["GET", "POST"])
@login_required
@permission_required("manage_inspections")
def new_inspection():

    form = InspectionForm()

    form.batch_id.choices = [

        (b.id, b.batch_number)

        for b in CableBatch.query.filter_by(

            company_id=current_user.company_id

        ).order_by(

            CableBatch.production_date.desc()

        ).all()

    ]

    if form.validate_on_submit():

        inspection = Inspection(

            company_id=current_user.company_id,

            inspection_number=generate_inspection_number(form.inspection_date.data),

            batch_id=form.batch_id.data,

            inspector=form.inspector.data,

            remarks=form.remarks.data,

            inspection_date=form.inspection_date.data

        )

        db.session.add(inspection)

        log_activity(

            module="Inspection",

            action="Create",

            description=f"Created inspection '{inspection.inspection_number}'"

        )

        db.session.commit()


        flash(
            "Inspection saved successfully.",
            "success"
        )

        if (
                current_user.notification_enabled
                and current_user.inspection_notification
        ):

            create_notification(

                title="Inspection pending",

                message=f"{inspection.inspection_number} is awaiting quality metric evaluation.",

                category="Inspection",

                priority="Normal",

                link=url_for(

                    "main.view_inspection",

                    inspection_id=inspection.id

                )

            )

        return redirect(
            url_for("main.inspections")
        )

    return render_template(
        "inspection_form.html",
        form=form
    )

@main.route("/inspections/<int:inspection_id>")
@permission_required("manage_inspections")
@login_required
def view_inspection(inspection_id):

    inspection = Inspection.query.filter_by(
        id=inspection_id,
        company_id=current_user.company_id
    ).first_or_404()

    return render_template(
        "inspection_details.html",
        inspection=inspection
    )

@main.route("/inspections/<int:inspection_id>/edit", methods=["GET", "POST"])
@login_required
@permission_required("manage_inspections")
def edit_inspection(inspection_id):

    inspection = Inspection.query.filter_by(
        id=inspection_id,
        company_id=current_user.company_id
    ).first_or_404()

    form = InspectionForm(obj=inspection)

    form.batch_id.choices = [

        (b.id, b.batch_number)

        for b in CableBatch.query.filter_by(

            company_id=current_user.company_id

        ).order_by(

            CableBatch.production_date.desc()

        ).all()

    ]

    if form.validate_on_submit():

        inspection.batch_id = form.batch_id.data
        inspection.inspector = form.inspector.data
        inspection.inspection_date = form.inspection_date.data
        inspection.remarks = form.remarks.data

        log_activity(

            module="Inspection",

            action="Update",

            description=f"Updated inspection '{inspection.inspection_number}'"

        )

        db.session.commit()

        flash(
            "Inspection updated successfully.",
            "success"
        )

        return redirect(url_for("main.inspections"))

    return render_template(
        "inspection_form.html",
        form=form
    )

@main.route("/inspections/<int:inspection_id>/delete")
@login_required
@permission_required("manage_inspections")
def delete_inspection(inspection_id):
    inspection = Inspection.query.filter_by(
        id=inspection_id,
        company_id=current_user.company_id
    ).first_or_404()


    log_activity(

        module="Inspection",

        action="Delete",

        description=f"Deleted inspection '{inspection.inspection_number}'"

    )

    db.session.delete(inspection)

    db.session.commit()

    flash(
        "Inspection deleted successfully.",
        "success"
    )

    return redirect(url_for("main.inspections"))

# ==========================================
# QUALITY METRICS
# ==========================================

@main.route("/quality-metrics")
@permission_required("manage_quality_metrics")
@login_required
def quality_metrics():
    metrics = (
        QualityMetric.query
        .filter_by(
            company_id=current_user.company_id
        )
        .join(Inspection)
        .order_by(
            Inspection.inspection_date.desc()
        )
        .all()
    )

    return render_template(
        "quality_metrics.html",
        metrics=metrics
    )


@main.route(
    "/quality-metrics/new/<int:inspection_id>",
    methods=["GET", "POST"]
)
@login_required
@permission_required("manage_quality_metrics")
def new_quality_metric(inspection_id):

    inspection = Inspection.query.filter_by(
        id=inspection_id,
        company_id=current_user.company_id
    ).first_or_404()

    form = QualityMetricForm()

    specifications = (
        QualitySpecification.query
        .filter_by(
            company_id=current_user.company_id,
            cable_type_id=inspection.batch.cable_type_id
        )
        .order_by(
            QualitySpecification.metric_name
        )
        .all()
    )

    form.specification_id.choices = [
        (
            s.id,
            s.metric_name
        )
        for s in specifications
    ]

    # --------------------------
    # Populate specification details
    # --------------------------

    if form.specification_id.data:

        spec = QualitySpecification.query.get(
            form.specification_id.data
        )

        if spec:

            form.unit.data = spec.unit

            form.minimum_value.data = spec.minimum_value

            form.maximum_value.data = spec.maximum_value

            form.expected_text.data = spec.expected_result

    if form.validate_on_submit():

        specification = QualitySpecification.query.filter_by(
            id=form.specification_id.data,
            company_id=current_user.company_id
        ).first_or_404()

        existing = QualityMetric.query.filter_by(
            company_id=current_user.company_id,
            inspection_id=inspection.id,
            specification_id=specification.id
        ).first()

        if existing:

            flash(
                "This quality metric has already been recorded.",
                "warning"
            )

            return redirect(
                url_for(
                    "main.view_inspection",
                    inspection_id=inspection.id
                )
            )

        measured = form.measured_value.data.strip()

        # --------------------------------
        # Automatic Validation
        # --------------------------------

        passed, result = validate_result(
            specification,
            measured
        )

        metric = QualityMetric(

            company_id=current_user.company_id,

            inspection_id=inspection.id,

            specification_id=specification.id,

            measured_value=measured,

            result=result

        )

        db.session.add(metric)

        # Generate the metric ID before using it
        db.session.flush()

        # --------------------------------
        # Automatically create deviation
        # --------------------------------

        deviation = None

        if metric.result == "Fail":

            existing_deviation = Deviation.query.filter_by(
                quality_metric_id=metric.id,
                company_id=current_user.company_id
            ).first()

            if existing_deviation: 
                
                deviation = existing_deviation 
                
            else: 
                
                deviation = Deviation( 
                    company_id=current_user.company_id, 
                    deviation_number=generate_deviation_number(), 
                    inspection_id=inspection.id, 
                    quality_metric_id=metric.id, 
                    description=( 
                        f"{specification.metric_name} " 
                        f"failed inspection." ), 
                    severity="Major", 
                    status="Open", 
                    reported_by=inspection.inspector 
                ) 
                
                db.session.add(deviation)

        log_activity(

            module="Quality Metric",

            action="Create",

            description=f"Recorded '{specification.metric_name}' for {inspection.inspection_number}"

        )

        db.session.commit()

        if (
                deviation is not None
                and current_user.notification_enabled
                and current_user.deviation_notification
        ):

            create_notification(

                title="Failed Metrics",

                message=f"A Deviation {deviation.deviation_number} was created for batch number {inspection.batch.batch_number}.",

                category="Deviation",

                priority="High",

                link=url_for(

                    "main.view_deviation",

                    deviation_id=deviation.id

                )

            )

        if result == "Fail":
            session["play_fail_sound"] = True

        old_status = inspection.overall_result

        update_inspection_status(
            inspection.id
        )

        db.session.refresh(
            inspection
        )

        if old_status != inspection.overall_result:

            if inspection.overall_result == "Pass":

                if (
                        current_user.notification_enabled
                        and current_user.inspection_notification
                ):

                    create_notification(

                        title="Inspection Passed",

                        message=f"{inspection.inspection_number} passed all quality checks.",

                        category="Inspection",

                        priority="Normal",

                        link=url_for(
                            "main.view_inspection",
                            inspection_id=inspection.id
                        )

                    )

            elif inspection.overall_result == "Fail":

                if (
                        current_user.notification_enabled
                        and current_user.inspection_notification
                ):

                    create_notification(

                        title="Inspection Failed",

                        message=f"{inspection.inspection_number} failed one or more quality checks.",

                        category="Inspection",

                        priority="High",

                        link=url_for(
                            "main.view_inspection",
                            inspection_id=inspection.id
                        )

                    )

        flash(
            "Quality Metric recorded successfully.",
            "success"
        )

        return redirect(
            url_for(
                "main.view_inspection",
                inspection_id=inspection.id
            )
        )

    return render_template(

        "quality_metric_form.html",

        form=form,

        inspection=inspection

    )


@main.route(
    "/quality-metrics/<int:metric_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@permission_required("manage_quality_metrics")
def edit_quality_metric(metric_id):

    metric = QualityMetric.query.filter_by(

        id=metric_id,

        company_id=current_user.company_id

    ).first_or_404()

    inspection = metric.inspection

    form = QualityMetricForm(obj=metric)

    specifications = (

        QualitySpecification.query

        .filter_by(

            company_id=current_user.company_id,

            cable_type_id=inspection.batch.cable_type_id

        )

        .order_by(

            QualitySpecification.metric_name

        )

        .all()

    )

    form.specification_id.choices = [

        (

            s.id,

            s.metric_name

        )

        for s in specifications

    ]

    if request.method == "GET":

        form.specification_id.data = metric.specification_id

        form.measured_value.data = metric.measured_value

        specification = metric.specification

        form.unit.data = specification.unit

        form.minimum_value.data = specification.minimum_value

        form.maximum_value.data = specification.maximum_value

        form.expected_text.data = specification.expected_result

    if form.validate_on_submit():

        metric.specification_id = form.specification_id.data

        metric.measured_value = form.measured_value.data.strip()

        specification = QualitySpecification.query.filter_by(

            id=metric.specification_id,

            company_id=current_user.company_id

        ).first_or_404()

        passed, result = validate_result(
            specification,
            metric.measured_value
        )

        metric.result = result

        existing_deviation = Deviation.query.filter_by(
            quality_metric_id=metric.id,
            company_id=current_user.company_id
        ).first()

        # Metric now FAILS
        if metric.result == "Fail":

            if not existing_deviation:
                deviation = Deviation(
                    company_id=current_user.company_id,
                    deviation_number=generate_deviation_number(),
                    inspection_id=inspection.id,
                    quality_metric_id=metric.id,
                    description=f"{specification.metric_name} failed inspection.",
                    severity="Major",
                    status="Open",
                    reported_by=inspection.inspector
                )

                db.session.add(deviation)

        # Metric now PASSES
        else:

            if existing_deviation:
                db.session.delete(existing_deviation)


        log_activity(

            module="Quality Metric",

            action="Update",

            description=f"Updated '{specification.metric_name}' for {inspection.inspection_number}"

        )

        db.session.commit()

        if result == "Fail":
            session["play_fail_sound"] = True

        old_status = inspection.overall_result

        update_inspection_status(

            inspection.id

        )

        db.session.refresh(

            inspection

        )

        if old_status != inspection.overall_result:

            if inspection.overall_result == "Pass":

                create_notification(

                    title="Inspection Passed",

                    message=f"{inspection.inspection_number} passed all quality checks.",

                    category="Inspection",

                    priority="Normal",

                    link=url_for(

                        "main.view_inspection",

                        inspection_id=inspection.id

                    )

                )

            elif inspection.overall_result == "Fail":

                create_notification(

                    title="Inspection Failed",

                    message=f"{inspection.inspection_number} failed one or more quality checks.",

                    category="Inspection",

                    priority="High",

                    link=url_for(

                        "main.view_inspection",

                        inspection_id=inspection.id

                    )

                )

        flash(

            "Quality Metric updated successfully.",

            "success"

        )

        return redirect(

            url_for(

                "main.view_inspection",

                inspection_id=inspection.id

            )

        )

    return render_template(

        "quality_metric_form.html",

        form=form,

        inspection=inspection

    )

@main.route(
    "/quality-metrics/<int:metric_id>/delete"
)
@login_required
@permission_required("manage_quality_metrics")
def delete_quality_metric(metric_id):
    metric = QualityMetric.query.filter_by(

        id=metric_id,

        company_id=current_user.company_id

    ).first_or_404()

    inspection_id = metric.inspection_id



    db.session.delete(metric)

    db.session.commit()

    inspection = Inspection.query.get(inspection_id)

    old_status = inspection.overall_result

    update_inspection_status(inspection_id)

    db.session.refresh(inspection)

    if old_status != inspection.overall_result:

        if inspection.overall_result == "Pass":

            create_notification(
                title="Inspection Passed",
                message=f"{inspection.inspection_number} passed all quality checks.",
                category="Inspection",
                priority="Normal",
                link=url_for(
                    "main.view_inspection",
                    inspection_id=inspection.id
                )
            )

        elif inspection.overall_result == "Fail":

            create_notification(
                title="Inspection Failed",
                message=f"{inspection.inspection_number} failed one or more quality checks.",
                category="Inspection",
                priority="High",
                link=url_for(
                    "main.view_inspection",
                    inspection_id=inspection.id
                )
            )
    flash(
        "Quality Metric deleted.",
        "success"
    )

    return redirect(

        url_for(

            "main.view_inspection",

            inspection_id=inspection_id

        )

    )

@main.route("/quality-specification/<int:specification_id>/details")
@login_required
def quality_specification_details(specification_id):

    specification = QualitySpecification.query.filter_by(

        id=specification_id,

        company_id=current_user.company_id

    ).first_or_404()

    return jsonify({

        "unit": specification.unit or "",

        "minimum_value": specification.minimum_value
            if specification.minimum_value is not None else "",

        "maximum_value": specification.maximum_value
            if specification.maximum_value is not None else "",

        "expected_result": specification.expected_result or ""

    })


@main.route("/quality-specifications/<int:id>/json")
@login_required
def quality_specification_json(id):

    specification = QualitySpecification.query.filter_by(
        id=id,
        company_id=current_user.company_id
    ).first_or_404()

    return {
        "unit": specification.unit,
        "minimum_value": specification.minimum_value,
        "maximum_value": specification.maximum_value,
        "expected_result": specification.expected_result,
        "validation_type": specification.validation_type
    }


@main.route("/quality-specifications")
@permission_required("manage_specifications")
@login_required
def quality_specifications():
    specifications = (
        QualitySpecification.query
        .join(CableType)
        .filter(
            QualitySpecification.company_id == current_user.company_id
        )
        .order_by(
            CableType.name,
            QualitySpecification.metric_name
        )
        .all()
    )

    return render_template(
        "quality_specifications.html",
        specifications=specifications
    )

@main.route(
    "/quality-specifications/new",
    methods=["GET", "POST"]
)
@login_required
@permission_required("manage_specifications")
def new_quality_specification():

    form = QualitySpecificationForm()

    cable_types = CableType.query.filter_by(
        company_id=current_user.company_id
    ).order_by(
        CableType.pair_count,
        CableType.conductor_size,
        CableType.name
    ).all()

    form.cable_type_id.choices = [
        (
            c.id,
            f"{c.pair_count} x {c.conductor_size} - {c.name}"
        )
        for c in cable_types
    ]

    voltage_map = {
        c.id: c.voltage_rating
        for c in cable_types
    }


    if form.validate_on_submit():

        specification = QualitySpecification(

            company_id=current_user.company_id,

            cable_type_id=form.cable_type_id.data,

            metric_name=form.metric_name.data,

            unit=form.unit.data,

            validation_type=form.validation_type.data,

            minimum_value=form.minimum_value.data or 0,

            maximum_value=form.maximum_value.data or 0,

            requirement=form.requirement.data,

            expected_result=form.expected_result.data,

            non_conformance_message=form.non_conformance_message.data

        )

        db.session.add(specification)

        log_activity(

            module="Quality Specification",

            action="Create",

            description=f"Added specification '{specification.metric_name}'"

        )

        db.session.commit()

        flash(
            "Quality Specification added successfully.",
            "success"
        )

        return redirect(
            url_for("main.quality_specifications")
        )

    existing = QualitySpecification.query.filter_by(
        company_id=current_user.company_id,
        cable_type_id=form.cable_type_id.data,
        metric_name=form.metric_name.data
    ).first()

    if existing:
        flash(
            "This specification already exists for the selected cable type.",
            "warning"
        )
    return render_template(
            "quality_specification_form.html",
            form=form,
            voltage_map = voltage_map

        )


@main.route(
    "/quality-specifications/<int:id>/edit",
    methods=["GET", "POST"]
)
@login_required
@permission_required("manage_specifications")
def edit_quality_specification(id):

    specification = QualitySpecification.query.filter_by(
        id=id,
        company_id=current_user.company_id
    ).first_or_404()

    form = QualitySpecificationForm(obj=specification)

    cable_types = CableType.query.filter_by(
        company_id=current_user.company_id
    ).order_by(
        CableType.pair_count,
        CableType.conductor_size,
        CableType.name
    ).all()

    form.cable_type_id.choices = [
        (
            c.id,
            f"{c.pair_count} X {c.conductor_size} - {c.name}"
        )
        for c in cable_types
    ]

    voltage_map = {
        c.id: c.voltage_rating
        for c in cable_types
    }


    if form.validate_on_submit():

        specification.cable_type_id = form.cable_type_id.data

        specification.metric_name = form.metric_name.data

        specification.unit = form.unit.data

        specification.validation_type = form.validation_type.data

        specification.minimum_value = form.minimum_value.data or 0

        specification.maximum_value = form.maximum_value.data or 0

        specification.requirement = form.requirement.data

        specification.expected_result = form.expected_result.data

        specification.non_conformance_message = (
            form.non_conformance_message.data
        )

        log_activity(

            module="Quality Specification",

            action="Update",

            description=f"Updated specification '{specification.metric_name}'"

        )

        db.session.commit()

        flash(
            "Specification updated successfully.",
            "success"
        )

        return redirect(
            url_for("main.quality_specifications")
        )

    existing = QualitySpecification.query.filter_by(
        company_id=current_user.company_id,
        cable_type_id=form.cable_type_id.data,
        metric_name=form.metric_name.data
    ).first()

    if existing:
        flash(
            "This specification already exists for the selected cable type.",
            "warning"
        )
    return render_template(
            "quality_specification_form.html",
            form=form,
            voltage_map=voltage_map
        )

@main.route("/quality-specifications/<int:id>/delete")
@login_required
@permission_required("manage_specifications")
def delete_quality_specification(id):

    specification = QualitySpecification.query.filter_by(
        id=id,
        company_id=current_user.company_id
    ).first_or_404()

    log_activity(

        module="Quality Specification",

        action="Delete",

        description=f"Deleted specification '{specification.metric_name}'"

    )

    db.session.delete(specification)

    db.session.commit()

    flash(
        "Specification deleted successfully.",
        "success"
    )

    return redirect(
        url_for("main.quality_specifications")
    )

@main.route("/deviations")
@login_required
@permission_required("manage_deviations")
def deviations():

    deviations = Deviation.query.filter_by(
        company_id=current_user.company_id
    ).order_by(
        Deviation.reported_date.desc()
    ).all()

    return render_template(
        "deviations.html",
        deviations=deviations
    )



@main.route("/deviations/<int:deviation_id>")
@login_required
def view_deviation(deviation_id):
    deviation = Deviation.query.filter_by(
        id=deviation_id,
        company_id=current_user.company_id
    ).first_or_404()

    return render_template(
        "view_deviation.html",
        deviation=deviation
    )

@main.route(
    "/deviations/<int:deviation_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@permission_required("manage_deviations")
def edit_deviation(deviation_id):
    deviation = Deviation.query.filter_by(
        id=deviation_id,
        company_id=current_user.company_id
    ).first_or_404()

    form = DeviationForm(obj=deviation)

    # Related records
    inspection = deviation.inspection
    metric = deviation.quality_metric
    specification = metric.specification

    if form.validate_on_submit():

        # Store the old status before updating
        old_status = deviation.status

        deviation.description = form.description.data

        deviation.severity = form.severity.data

        deviation.root_cause = form.root_cause.data

        deviation.status = form.status.data

        deviation.reported_by = form.reported_by.data

        if old_status != "Closed" and deviation.status == "Closed":

            deviation.closed_date = datetime.utcnow().date()

        elif deviation.status != "Closed":

            deviation.closed_date = None

        # Audit Log
        if old_status != "Closed" and deviation.status == "Closed":

            log_activity(

                module="Deviation",

                action="Close",

                description=(
                    f"{current_user.full_name} closed "
                    f"Deviation '{deviation.deviation_number}' "
                    f"(Severity: {deviation.severity})"
                )

            )

        else:

            log_activity(

                module="Deviation",

                action="Update",

                description=(
                    f"{current_user.full_name} updated "
                    f"Deviation '{deviation.deviation_number}'"
                )

            )

        db.session.commit()

        flash(
            "Deviation updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "main.view_deviation",
                deviation_id=deviation.id
            )
        )

    return render_template(
        "deviation_form.html",
        form=form,
        deviation=deviation,
        inspection=inspection,
        metric=metric,
        specification=specification
    )


@main.route("/deviations/<int:deviation_id>/delete")
@login_required
@permission_required("manage_deviations")
def delete_deviation(deviation_id):
    deviation = Deviation.query.filter_by(
        id=deviation_id,
        company_id=current_user.company_id
    ).first_or_404()

    log_activity(

        module="Deviation",

        action="Delete",

        description=(
            f"{current_user.full_name} deleted "
            f"Deviation '{deviation.deviation_number}'"
        )

    )

    db.session.delete(deviation)

    db.session.commit()

    flash(
        "Deviation deleted successfully.",
        "success"
    )

    return redirect(
        url_for("main.deviations")
    )



@main.route("/capa")
@permission_required("manage_capa")
@login_required
def capa():

    capas = CAPA.query.filter_by(
        company_id=current_user.company_id
    ).order_by(
        CAPA.created_at.desc()
    ).all()

    changed = False

    for c in capas:

        old_status = c.status

        update_capa_status(c)

        if old_status != c.status:
            changed = True

        c.display_status = c.status
        c.days_overdue = get_days_overdue(c)

    if changed:
        db.session.commit()

    return render_template(
        "capa.html",
        capas=capas
    )

@main.route(
    "/capa/new/<int:deviation_id>",
    methods=["GET", "POST"]
)
@login_required
@permission_required("manage_capa")
def new_capa(deviation_id):

    deviation = Deviation.query.filter_by(
        id=deviation_id,
        company_id=current_user.company_id
    ).first_or_404()

    existing = CAPA.query.filter_by(
        deviation_id=deviation.id
    ).first()

    if existing:

        flash(
            "A CAPA already exists for this deviation.",
            "warning"
        )

        return redirect(
            url_for(
                "main.view_capa",
                capa_id=existing.id
            )
        )

    form = CAPAForm()

    if form.validate_on_submit():

        capa = CAPA(

            company_id=current_user.company_id,

            deviation_id=deviation.id,

            corrective_action=form.corrective_action.data,

            preventive_action=form.preventive_action.data,

            assigned_to=form.assigned_to.data,

            due_date=form.due_date.data,

            completion_date=form.completion_date.data,

            effectiveness=form.effectiveness.data,

            status=form.status.data

        )

        db.session.add(capa)
        log_activity(

            module="CAPA",

            action="Create",

            description=(
                f"{current_user.full_name} created "
                f"CAPA for deviation '{deviation.deviation_number}'"
            )

        )

        db.session.commit()

        flash(
            "CAPA created successfully.",
            "success"
        )

        if (
                current_user.notification_enabled
                and current_user.capa_notification
        ):

            create_notification(

                title="New CAPA",

                message=f"CAPA created for {capa.deviation.deviation_number}.",

                category="CAPA",

                priority="Normal",

                link=url_for(

                    "main.view_capa",

                    capa_id=capa.id

                )

            )

        return redirect(
            url_for(
                "main.view_capa",
                capa_id=capa.id
            )
        )

    return render_template(
        "capa_form.html",
        form=form,
        deviation=deviation
    )

@main.route("/capa/<int:capa_id>")
@permission_required("manage_capa")
@login_required
def view_capa(capa_id):

    capa = CAPA.query.filter_by(
        id=capa_id,
        company_id=current_user.company_id
    ).first_or_404()

    capa.display_status = get_capa_status(
        capa
    )

    capa.days_overdue = get_days_overdue(
        capa
    )

    return render_template(
        "view_capa.html",
        capa=capa
    )

@main.route(
    "/capa/<int:capa_id>/edit",
    methods=["GET", "POST"]
)
@login_required
@permission_required("manage_capa")
def edit_capa(capa_id):

    capa = CAPA.query.filter_by(
        id=capa_id,
        company_id=current_user.company_id
    ).first_or_404()

    form = CAPAForm(obj=capa)

    if form.validate_on_submit():

        # Store the previous status
        old_status = capa.status

        # Update fields
        capa.corrective_action = form.corrective_action.data

        capa.preventive_action = form.preventive_action.data

        capa.assigned_to = form.assigned_to.data

        capa.due_date = form.due_date.data

        capa.completion_date = form.completion_date.data

        capa.status = form.status.data

        capa.effectiveness = form.effectiveness.data

        # Audit Trail
        if old_status != "Closed" and capa.status == "Closed":

            log_activity(

                module="CAPA",

                action="Close",

                description=(
                    f"{current_user.full_name} closed "
                    f"CAPA for deviation '{capa.deviation.deviation_number}'"
                )

            )

        else:

            log_activity(

                module="CAPA",

                action="Update",

                description=(
                    f"{current_user.full_name} closed "
                    f"CAPA for deviation '{capa.deviation.deviation_number}'"
                )

            )

        db.session.commit()

        flash(
            "CAPA updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "main.view_capa",
                capa_id=capa.id
            )
        )

    return render_template(
        "capa_form.html",
        form=form,
        deviation=capa.deviation
    )


@main.route("/capa/<int:capa_id>/delete")
@login_required
@permission_required("manage_capa")
def delete_capa(capa_id):

    capa = CAPA.query.filter_by(
        id=capa_id,
        company_id=current_user.company_id
    ).first_or_404()

    log_activity(

        module="CAPA",

        action="Delete",

        description=(
            f"{current_user.full_name} deleted "
            f"CAPA for deviation '{capa.deviation.deviation_number}'"
        )

    )

    db.session.delete(capa)

    db.session.commit()

    flash(
        "CAPA deleted successfully.",
        "success"
    )

    return redirect(
        url_for("main.capa")
    )

@main.route("/notifications")
@permission_required("manage_notifications")
@login_required
def notifications():
    notifications = Notification.query.filter_by(
        company_id=current_user.company_id,
        user_id=current_user.id
    ).order_by(
        Notification.created_at.desc()
    ).all()

    return render_template(

        "notifications.html",

        notifications=notifications

    )
@main.route("/notifications/<int:notification_id>/read")
@login_required
def read_notification(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        company_id=current_user.company_id,
        user_id=current_user.id
    ).first_or_404()

    notification.is_read = True

    db.session.commit()

    if notification.link:

        return redirect(notification.link)

    return redirect(

        url_for("main.notifications")

    )

@main.route("/notifications/read-all")
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(
        company_id=current_user.company_id,
        user_id=current_user.id,
        is_read=False
    ).update(
        {
            "is_read": True
        }
    )

    db.session.commit()

    flash(

        "All notifications marked as read.",

        "success"

    )

    return redirect(

        url_for("main.notifications")

    )


@main.route("/notifications/<int:notification_id>/delete")
@login_required
def delete_notification(notification_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        company_id=current_user.company_id,
        user_id=current_user.id
    ).first_or_404()

    log_activity(

        module="Notification",

        action="Delete",

        description=(
            f"{current_user.full_name} deleted "
            f"notification '{notification.title}'"
        )

    )

    db.session.delete(notification)

    db.session.commit()

    flash(

        "Notification deleted.",

        "success"

    )

    return redirect(

        url_for("main.notifications")

    )

@main.route("/audit-trail")
@permission_required("view_audit")
@login_required

def audit_trail():

    logs = AuditLog.query

    # Search
    search = request.args.get("search", "")

    if search:

        logs = logs.filter(

            AuditLog.description.ilike(f"%{search}%")

        )

    # Module Filter
    module = request.args.get("module", "")

    if module:

        logs = logs.filter(

            AuditLog.module == module

        )

    # Action Filter
    action = request.args.get("action", "")

    if action:

        logs = logs.filter(

            AuditLog.action == action

        )

    logs = logs.order_by(

        AuditLog.created_at.desc()

    ).all()

    return render_template(

        "audit_trail.html",

        logs=logs,

        search=search,

        module=module,

        action=action

    )

@main.route("/reports")
@permission_required("view_reports")
@login_required
def reports():

    inspection_count = Inspection.query.filter_by(
        company_id=current_user.company_id
    ).count()

    deviation_count = Deviation.query.filter_by(
        company_id=current_user.company_id
    ).count()

    open_capa = CAPA.query.filter_by(
        company_id=current_user.company_id,
        status="Open"
    ).count()

    audit_count = AuditLog.query.filter_by(
        company_id=current_user.company_id
    ).count()

    reports = [

        {
            "title": "Inspection Report",
            "description": "View inspection activities and quality results.",
            "icon": "bi bi-clipboard-check",
            "color": "primary",
            "endpoint": "main.inspection_report"
        },

        {
            "title": "Deviation Report",
            "description": "Analyze deviations by status and severity.",
            "icon": "bi bi-exclamation-triangle",
            "color": "danger",
            "endpoint": "main.deviation_report"
        },

        {
            "title": "CAPA Report",
            "description": "Monitor corrective and preventive actions.",
            "icon": "bi bi-tools",
            "color": "warning",
            "endpoint": "main.capa_report"
        },

        {
            "title": "Quality Metrics Report",
            "description": "Review quality measurements and trends.",
            "icon": "bi bi-graph-up-arrow",
            "color": "success",
            "endpoint": "main.quality_metrics_report"
        },

        {
            "title": "Production Report",
            "description": "Production batches and line performance.",
            "icon": "bi bi-building-gear",
            "color": "secondary",
            "endpoint": "main.production_report"
        },

        {
            "title": "Customer Report",
            "description": "Customer inspection and quality history.",
            "icon": "bi bi-people",
            "color": "info",
            "endpoint": "main.customer_report"
        },

        {
            "title": "User Report",
            "description": "User activities and account summary.",
            "icon": "bi bi-person-badge",
            "color": "secondary",
            "endpoint": "main.user_report"
        },

        {
            "title": "Audit Trail",
            "description": "Complete system activity log.",
            "icon": "bi bi-journal-text",
            "color": "success",
            "endpoint": "main.audit_report"
        }

    ]

    if current_user.role == "System Administrator":

        reports.append({

            "title": "Company Report",

            "description": "Company performance and statistics.",

            "icon": "bi bi-building",

            "color": "primary",

            "endpoint": "main.company_report"

        })

    return render_template(

        "reports/reports.html",

        reports=reports,

        inspection_count=inspection_count,

        deviation_count=deviation_count,

        open_capa=open_capa,

        audit_count=audit_count

    )

# ============================================================
# REPORTS
# ============================================================

@main.route("/reports/inspections")
@login_required
def inspection_report():
    query = get_filtered_inspection_query(

        current_user.company_id

    )

    query = apply_inspection_sort(

        query

    )

    # --------------------------
    # Pagination
    # --------------------------

    pagination = paginate_query(

        query

    )

    inspections = pagination.items
    # --------------------------
    # Statistics
    # --------------------------

    stats = get_inspection_statistics(

        query

    )

    result_chart = get_result_chart_data(

        query

    )

    monthly_chart = get_monthly_trend(

        current_user.company_id

    )

    line_chart = get_production_line_chart(

        current_user.company_id

    )

    cable_chart = get_cable_type_chart(

        current_user.company_id

    )

    # --------------------------
    # Dropdowns
    # --------------------------

    customers = Customer.query.filter_by(

        company_id=current_user.company_id

    ).order_by(

        Customer.company_name

    ).all()

    cable_types = CableType.query.filter_by(

        company_id=current_user.company_id

    ).order_by(

        CableType.name

    ).all()

    production_lines = ProductionLine.query.filter_by(

        company_id=current_user.company_id

    ).order_by(

        ProductionLine.line_name

    ).all()

    inspectors = db.session.query(

        Inspection.inspector

    ).filter_by(

        company_id=current_user.company_id

    ).distinct().order_by(

        Inspection.inspector

    ).all()

    return render_template(
        "reports/inspection_report.html",

        inspections=inspections,

        pagination=pagination,

        result_chart=result_chart,

        monthly_chart=monthly_chart,

        line_chart=line_chart,

        cable_chart=cable_chart,

        total=stats["total"],

        passed=stats["passed"],

        failed=stats["failed"],

        pending=stats["pending"],

        pass_rate=stats["pass_rate"]
    )

@main.route("/reports/inspections/excel")
@login_required
def export_inspection_excel():

    query = get_filtered_inspection_query(

        current_user.company_id

    )

    query = apply_inspection_sort(

        query

    )

    inspections = query.all()

    headers = [

        "Inspection Number",

        "Cable Name",

        "Voltage Rating",

        "Drain Config",

        "Length (m)",

        "Customer",

        "Batch No",

        "Drum No",

        "Cable Code",

        "Production Line",

        "Inspector",

        "Inspection Date",

        "Result",

        "Remarks"

    ]
    rows = []

    for inspection in inspections:
        cable = inspection.batch.cable_type
        batch = inspection.batch

        rows.append([

            inspection.inspection_number,

            f"{cable.pair_count} x {cable.conductor_size} -\n{cable.name}",

            cable.voltage_rating,

            cable.drain_configuration,

            batch.cable_length,

            f"{batch.customer.company_name}\n{batch.customer.address}",

            batch.batch_number,

            batch.drum_number,

            batch.cable_code,

            batch.production_line.line_name,

            inspection.inspector,

            inspection.inspection_date.strftime("%d-%b-%Y"),

            inspection.overall_result,

            inspection.remarks

        ])

    print(headers)
    print(type(headers))

    return export_excel(

        title="Inspection Report",

        headers=headers,

        rows=rows,

        filename="Inspection_Report.xlsx"

    )


@main.route("/reports/inspections/pdf")
@login_required
def export_inspection_pdf():

    query = get_filtered_inspection_query(

        current_user.company_id

    )

    query = apply_inspection_sort(

        query

    )

    inspections = query.all()

    #pdf header
    headers = [

        "Inspection No",

        "Cable Name",

        "Rating",

        "Drain Config",

        "Length",

        "Customer",

        "Batch No",

        "Drum No",

        "Cable Code",

        "Line",

        "Inspector",

        "Date",

        "Result",


    ]
    #pdf row

    rows = []

    for inspection in inspections:
        cable = inspection.batch.cable_type
        batch = inspection.batch

        rows.append([

            inspection.inspection_number,

            f"{cable.pair_count} x {cable.conductor_size} -\n{cable.name}",

            cable.voltage_rating,

            cable.drain_configuration,

            f"{batch.cable_length} m",

            f"{batch.customer.company_name}\n{batch.customer.address}",

            batch.batch_number,

            batch.drum_number,

            batch.cable_code,

            batch.production_line.line_name,

            inspection.inspector,

            inspection.inspection_date.strftime("%d-%b-%Y"),

            inspection.overall_result,


        ])

    #Export PDF

    return export_pdf(

        title="Inspection Report",

        headers=headers,

        rows=rows,

        filename="Inspection_Report.pdf"

    )



@main.route("/reports/deviations")

@login_required

def deviation_report():

    query = get_filtered_deviation_query(

        current_user.company_id

    )

    query = apply_deviation_sort(

        query

    )

    pagination = paginate_query(

        query

    )

    deviations = pagination.items

    stats = get_deviation_statistics(

        query

    )

    status_chart = get_deviation_chart(

        query

    )

    severity_chart = get_severity_chart(

        query

    )

    return render_template(

        "reports/deviation_report.html",

        deviations=deviations,

        pagination=pagination,

        total=stats["total"],

        open_count=stats["open"],

        progress=stats["progress"],

        closed=stats["closed"],

        critical=stats["critical"],

        status_chart=status_chart,

        severity_chart=severity_chart

    )

@main.route("/reports/deviations/excel")

@login_required

def export_deviation_excel():

    query = get_filtered_deviation_query(

        current_user.company_id

    )

    query = apply_deviation_sort(

        query

    )

    deviations = query.all()

    headers = [

        "Deviation No",

        "Inspection",

        "Severity",

        "Status",

        "Reported By",

        "Created",

        "Closed"

    ]

    rows = build_rows(

        deviations,

        [

            "deviation_number",

            "inspection.inspection_number",

            "severity",

            "status",

            "reported_by",

            "created_at",

            "closed_date"

        ]

    )

    return export_excel(

        title="Deviation Report",

        headers=headers,

        rows=rows,

        filename="Deviation_Report.xlsx"

    )

@main.route("/reports/deviations/pdf")

@login_required

def export_deviation_pdf():

    query = get_filtered_deviation_query(

        current_user.company_id

    )

    query = apply_deviation_sort(

        query

    )

    deviations = query.all()

    headers = [

        "Deviation No",

        "Inspection",

        "Severity",

        "Status",

        "Reported By"

    ]

    rows = build_rows(

        deviations,

        [

            "deviation_number",

            "inspection.inspection_number",

            "severity",

            "status",

            "reported_by"

        ]

    )

    return export_pdf(

        title="Deviation Report",

        headers=headers,

        rows=rows,

        filename="Deviation_Report.pdf"

    )


@main.route("/reports/capa")
@login_required
def capa_report():

    query = get_filtered_capa_query(

        current_user.company_id

    )

    query = apply_capa_sort(

        query

    )

    pagination = paginate_query(

        query

    )

    capas = pagination.items

    stats = get_capa_statistics(

        query

    )

    status_chart = get_capa_status_chart(

        query

    )

    effectiveness_chart = get_capa_effectiveness_chart(
        query
    )

    return render_template(

        "reports/capa_report.html",

        capas=capas,

        pagination=pagination,

        total=stats["total"],

        open_count=stats["open"],

        progress=stats["progress"],

        completed=stats["completed"],

        closed=stats["closed"],

        overdue=stats["overdue"],

        status_chart=status_chart,

        effectiveness_chart=effectiveness_chart

    )

@main.route("/reports/capa/excel")
@login_required
def export_capa_excel():

    query = get_filtered_capa_query(

        current_user.company_id

    )

    query = apply_capa_sort(

        query

    )

    capas = query.all()

    headers = [

        "CAPA ID",

        "Deviation",

        "Assigned To",

        "Status",

        "Effectiveness",

        "Due Date",

        "Completion Date"

    ]

    rows = build_rows(

        capas,

        [

            "id",

            "deviation.deviation_number",

            "assigned_to",

            "status",

            "effectiveness",

            "due_date",

            "completion_date"

        ]

    )

    return export_excel(

        title="CAPA Report",

        headers=headers,

        rows=rows,

        filename="CAPA_Report.xlsx"

    )

@main.route("/reports/capa/pdf")
@login_required
def export_capa_pdf():

    query = get_filtered_capa_query(

        current_user.company_id

    )

    query = apply_capa_sort(

        query

    )

    capas = query.all()

    headers = [

        "CAPA ID",

        "Deviation",

        "Assigned To",

        "Status",

        "Effectiveness"

    ]

    rows = build_rows(

        capas,

        [

            "id",

            "deviation.deviation_number",

            "assigned_to",

            "status",

            "effectiveness"

        ]

    )

    return export_pdf(

        title="CAPA Report",

        headers=headers,

        rows=rows,

        filename="CAPA_Report.pdf"

    )

@main.route("/reports/quality-metrics")
@login_required
def quality_metrics_report():

    query = get_filtered_quality_metric_query(

        current_user.company_id

    )

    query = apply_quality_metric_sort(

        query

    )

    pagination = paginate_query(

        query

    )

    metrics = pagination.items

    stats = get_quality_metric_statistics(

        query

    )

    chart = get_quality_metric_chart(

        query

    )

    return render_template(

        "reports/quality_metrics_report.html",

        metrics=metrics,

        pagination=pagination,

        total=stats["total"],

        passed=stats["passed"],

        failed=stats["failed"],

        chart=chart

    )

@main.route("/reports/quality-metrics/excel")
@login_required
def export_quality_metric_excel():

    query = get_filtered_quality_metric_query(

        current_user.company_id

    )

    query = apply_quality_metric_sort(

        query

    )

    metrics = query.all()

    headers = [

        "Inspection",

        "Metric",

        "Measured Value",

        "Unit",

        "Minimum",

        "Maximum",

        "Result"

    ]

    rows = []

    for metric in metrics:

        rows.append(

            [

                metric.inspection.inspection_number,

                metric.specification.metric_name,

                metric.measured_value,

                metric.specification.unit,

                metric.specification.minimum_value,

                metric.specification.maximum_value,

                metric.result

            ]

        )

    return export_excel(

        title="Quality Metrics Report",

        headers=headers,

        rows=rows,

        filename="Quality_Metrics_Report.xlsx"

    )

@main.route("/reports/quality-metrics/pdf")
@login_required
def export_quality_metric_pdf():

    query = get_filtered_quality_metric_query(

        current_user.company_id

    )

    query = apply_quality_metric_sort(

        query

    )

    metrics = query.all()

    headers = [

        "Inspection",

        "Metric",

        "Measured",

        "Result"

    ]

    rows = []

    for metric in metrics:

        rows.append(

            [

                metric.inspection.inspection_number,

                metric.specification.metric_name,

                f"{metric.measured_value} {metric.specification.unit}",

                metric.result

            ]

        )

    return export_pdf(

        title="Quality Metrics Report",

        headers=headers,

        rows=rows,

        filename="Quality_Metrics_Report.pdf"

    )



@main.route("/reports/production")
@login_required
def production_report():

    query = get_filtered_production_query(

        current_user.company_id

    )

    query = apply_production_sort(

        query

    )

    pagination = paginate_query(

        query

    )

    batches = pagination.items

    stats = get_production_statistics(

        query

    )

    chart = get_production_status_chart(

        query

    )

    return render_template(

        "reports/production_report.html",

        batches=batches,

        pagination=pagination,

        total=stats["total"],

        pending=stats["pending"],

        completed=stats["completed"],

        rejected=stats["rejected"],

        total_length=stats["total_length"],

        chart=chart

    )

@main.route("/reports/production/excel")
@login_required
def export_production_excel():

    query = get_filtered_production_query(

        current_user.company_id

    )

    query = apply_production_sort(

        query

    )

    batches = query.all()

    headers = [

        "Batch",

        "Drum",

        "Customer",

        "Cable Name",

        "Production Line",

        "Production Date",

        "Length",

        "Status"

    ]

    rows = []

    for batch in batches:

        rows.append([

            batch.batch_number,

            batch.drum_number,

            f"{batch.customer.company_name} \n{batch.customer.address}",

            f"{batch.cable_type.pair_count} x {batch.cable_type.conductor_size} -\n {batch.cable_type.name}",

            batch.production_line.line_name,

            batch.production_date,

            batch.cable_length,

            batch.status

        ])

    return export_excel(

        title="Production Report",

        headers=headers,

        rows=rows,

        filename="Production_Report.xlsx"

    )

@main.route("/reports/production/pdf")
@login_required
def export_production_pdf():

    query = get_filtered_production_query(

        current_user.company_id

    )

    query = apply_production_sort(

        query

    )

    batches = query.all()

    headers = [

        "Batch",

        "Customer",

        "Cable Name",

        "Status"

    ]

    rows = []

    for batch in batches:

        rows.append([

            batch.batch_number,

            f"{batch.customer.company_name} \n{batch.customer.address}",

            f"{batch.cable_type.pair_count} x {batch.cable_type.conductor_size} \n- {batch.cable_type.name}",

            batch.status

        ])

    return export_pdf(

        title="Production Report",

        headers=headers,

        rows=rows,

        filename="Production_Report.pdf"

    )


@main.route("/reports/customers")
@login_required
def customer_report():

    query = get_filtered_customer_query(

        current_user.company_id

    )

    query = apply_customer_sort(

        query

    )

    pagination = paginate_query(

        query

    )

    customers = pagination.items

    for customer in customers:
        customer.request_count = CableBatch.query.filter(
            CableBatch.customer_id == customer.id,
            CableBatch.status != "Rejected"
        ).count()

    stats = get_customer_statistics(

        query

    )

    request_chart = get_customer_request_chart(
        current_user.company_id
    )

    total_requests = CableBatch.query.filter(
        CableBatch.company_id == current_user.company_id,
        CableBatch.status != "Rejected"
    ).count()

    return render_template(

        "reports/customer_report.html",

        customers=customers,

        pagination=pagination,

        total=stats["total"],

        with_email=stats["with_email"],

        with_phone=stats["with_phone"],

        total_requests=total_requests,

        request_chart=request_chart

    )

@main.route("/reports/customers/excel")
@login_required
def export_customer_excel():

    query = get_filtered_customer_query(

        current_user.company_id

    )

    query = apply_customer_sort(

        query

    )

    customers = query.all()

    headers = [

        "Company",

        "Requests",

        "Contact Person",

        "Email",

        "Phone",

        "Address"

    ]

    rows = []

    for customer in customers:
        request_count = CableBatch.query.filter(
            CableBatch.customer_id == customer.id,
            CableBatch.status != "Rejected"
        ).count()

        rows.append([

            customer.company_name,

            request_count,

            customer.contact_person,

            customer.email,

            customer.phone,

            customer.address

        ])

    return export_excel(

        title="Customer Report",

        headers=headers,

        rows=rows,

        filename="Customer_Report.xlsx"

    )

@main.route("/reports/customers/pdf")
@login_required
def export_customer_pdf():

    query = get_filtered_customer_query(

        current_user.company_id

    )

    query = apply_customer_sort(

        query

    )

    customers = query.all()

    headers = [

        "Company",

        "Requests",

        "Contact",

        "Phone"

    ]

    rows = []

    for customer in customers:
        request_count = CableBatch.query.filter(
            CableBatch.customer_id == customer.id,
            CableBatch.status != "Rejected"
        ).count()

        rows.append([

            customer.company_name,

            request_count,

            customer.contact_person,

            customer.phone

        ])

    return export_pdf(

        title="Customer Report",

        headers=headers,

        rows=rows,

        filename="Customer_Report.pdf"

    )


@main.route("/reports/users")
@login_required
def user_report():

    query = get_filtered_user_query(

        current_user.company_id

    )

    query = apply_user_sort(

        query

    )

    pagination = paginate_query(

        query

    )

    users = pagination.items

    stats = get_user_statistics(

        query

    )

    chart = get_user_status_chart(

        query

    )

    return render_template(

        "reports/user_report.html",

        users=users,

        pagination=pagination,

        total=stats["total"],

        active=stats["active"],

        inactive=stats["inactive"],

        admins=stats["admins"],

        chart=chart

    )

@main.route("/reports/users/excel")
@login_required
def export_user_excel():

    query = get_filtered_user_query(

        current_user.company_id

    )

    query = apply_user_sort(

        query

    )

    users = query.all()

    headers = [

        "Name",

        "Email",

        "Role",

        "Status",

        "Created"

    ]

    rows = []

    for user in users:
        rows.append([

            user.full_name,

            user.email,

            user.role,

            "Active" if user.is_active else "Inactive",

            user.created_at.strftime(

                "%d-%m-%Y"

            )

        ])
    return export_excel(

        title="User Report",

        headers=headers,

        rows=rows,

        filename="User_Report.xlsx"

    )

@main.route("/reports/users/pdf")
@login_required
def export_user_pdf():

    query = get_filtered_user_query(

        current_user.company_id

    )

    query = apply_user_sort(

        query

    )

    users = query.all()

    headers = [

        "Name",

        "Email",

        "Role",

        "Status"

    ]

    rows = []

    for user in users:
        rows.append([

            user.full_name,

            user.email,

            user.role,

            "Active"

            if user.is_active

            else "Inactive"

        ])

    return export_pdf(

        title="User Report",

        headers=headers,

        rows=rows,

        filename="User_Report.pdf"

    )



@main.route("/reports/audit")
@login_required
def audit_report():

    query = get_filtered_audit_query(

        current_user.company_id

    )

    query = apply_audit_sort(

        query

    )

    pagination = paginate_query(

        query

    )

    logs = pagination.items

    stats = get_audit_statistics(

        query

    )

    chart = get_audit_chart(

        query

    )

    return render_template(

        "reports/audit_report.html",

        logs=logs,

        pagination=pagination,

        total=stats["total"],

        modules=stats["modules"],

        actions=stats["actions"],

        users=stats["users"],

        chart=chart

    )

@main.route("/reports/audit/excel")
@login_required
def export_audit_excel():

    query = get_filtered_audit_query(

        current_user.company_id

    )

    query = apply_audit_sort(

        query

    )

    logs = query.all()

    headers = [

        "Date",

        "User",

        "Module",

        "Action",

        "Description"

    ]

    rows = []

    for log in logs:

        rows.append([

            log.created_at.strftime(

                "%d-%m-%Y %H:%M"

            ),

            log.user.full_name

            if log.user else "",

            log.module,

            log.action,

            log.description or ""

        ])

    return export_excel(

        title="Audit Trail Report",

        headers=headers,

        rows=rows,

        filename="Audit_Trail_Report.xlsx"

    )

@main.route("/reports/audit/pdf")
@login_required
def export_audit_pdf():

    query = get_filtered_audit_query(

        current_user.company_id

    )

    query = apply_audit_sort(

        query

    )

    logs = query.all()

    headers = [

        "Date",

        "User",

        "Module",

        "Action"

    ]

    rows = []

    for log in logs:

        rows.append([

            log.created_at.strftime(

                "%d-%m-%Y %H:%M"

            ),

            log.user.full_name

            if log.user else "",

            log.module,

            log.action

        ])

    return export_pdf(

        title="Audit Trail Report",

        headers=headers,

        rows=rows,

        filename="Audit_Trail_Report.pdf"

    )


@main.route("/reports/company")
@login_required
@system_admin_required
def company_report():

    return render_template(
        "reports/company_report.html"
    )

@main.route("/settings")
@login_required
def settings():

    return render_template(
        "settings/settings.html"
    )

@main.route("/settings/appearance", methods=["GET", "POST"])
@login_required
def appearance_settings():

    form = ThemeSettingsForm()

    if request.method == "GET":
        form.theme.data = current_user.theme

    if form.validate_on_submit():

        current_user.theme = form.theme.data

        db.session.commit()

        flash(
            "Appearance settings updated successfully.",
            "success"
        )

        return redirect(
            url_for("main.appearance_settings")
        )

    return render_template(
        "settings/appearance.html",
        form=form
    )


@main.route(
    "/settings/account",
    methods=["GET", "POST"]
)
@login_required
def account_settings():

    form = AccountSettingsForm()

    if request.method == "GET":

        form.full_name.data = current_user.full_name
        form.username.data = current_user.username
        form.email.data = current_user.email

    if form.validate_on_submit():

        existing_username = User.query.filter(
            User.company_id == current_user.company_id,
            User.username == form.username.data,
            User.id != current_user.id
        ).first()

        if existing_username:

            flash(
                "Username already exists.",
                "danger"
            )

            return render_template(
                "settings/account.html",
                form=form
            )

        existing_email = User.query.filter(
            User.company_id == current_user.company_id,
            User.email == form.email.data,
            User.id != current_user.id
        ).first()

        if existing_email:

            flash(
                "Email already exists.",
                "danger"
            )

            return render_template(
                "settings/account.html",
                form=form
            )

        current_user.full_name = form.full_name.data
        current_user.username = form.username.data
        current_user.email = form.email.data

        log_activity(

            module="Settings",

            action="Account Settings",

            description=f"{current_user.full_name} updated account profile."

        )

        db.session.commit()

        flash(
            "Profile updated successfully.",
            "success"
        )

        return redirect(
            url_for("main.account_settings")
        )

    return render_template(
        "settings/account.html",
        form=form
    )


@main.route(
    "/settings/password",
    methods=["GET", "POST"]
)
@login_required
def password_settings():

    form = ChangePasswordForm()

    if form.validate_on_submit():

        if not current_user.check_password(form.current_password.data):

            flash(
                "Current password is incorrect.",
                "danger"
            )

            return render_template(
                "settings/password.html",
                form=form
            )

        if current_user.check_password(form.new_password.data):

            flash(
                "New password cannot be the same as your current password.",
                "warning"
            )

            return render_template(
                "settings/password.html",
                form=form
            )

        current_user.set_password(
            form.new_password.data
        )

        log_activity(

            module="Settings",

            action="Password Change",

            description=f"{current_user.full_name} changed account password."

        )

        db.session.commit()



        flash(
            "Password changed successfully.",
            "success"
        )

        return redirect(
            url_for("main.password_settings")
        )

    return render_template(
        "settings/password.html",
        form=form
    )


@main.route(
    "/settings/notifications",
    methods=["GET", "POST"]
)
@login_required
def notification_settings():

    form = NotificationSettingsForm()

    if request.method == "GET":

        form.notification_enabled.data = current_user.notification_enabled

        form.inspection_notification.data = current_user.inspection_notification

        form.deviation_notification.data = current_user.deviation_notification

        form.capa_notification.data = current_user.capa_notification

        form.failure_sound.data = current_user.failure_sound

    if form.validate_on_submit():

        current_user.notification_enabled = form.notification_enabled.data

        current_user.inspection_notification = form.inspection_notification.data

        current_user.deviation_notification = form.deviation_notification.data

        current_user.capa_notification = form.capa_notification.data

        current_user.failure_sound = form.failure_sound.data

        log_activity(

            module="Settings",

            action="Notification Settings",

            description=f"{current_user.full_name} updated notification preferences."

        )


        db.session.commit()



        flash(
            "Notification settings updated successfully.",
            "success"
        )

        return redirect(
            url_for("main.notification_settings")
        )

    return render_template(
        "settings/notifications.html",
        form=form
    )


@main.route("/search/live")
@login_required
def live_search():

    q = request.args.get("q", "").strip()

    if len(q) < 2:
        return jsonify([])

    results = []

    # Batch
    batches = CableBatch.query.filter(
        CableBatch.company_id == current_user.company_id,
        CableBatch.batch_number.ilike(f"%{q}%")
    ).limit(5)

    for b in batches:
        results.append({
            "type": "Batch",
            "title": b.batch_number,
            "url": url_for(
                "main.edit_batch",
                batch_id=b.id
            )
        })

    # Inspection
    inspections = Inspection.query.filter(
        Inspection.company_id == current_user.company_id,
        Inspection.inspection_number.ilike(f"%{q}%")
    ).limit(5)

    for i in inspections:
        results.append({
            "type": "Inspection",
            "title": i.inspection_number,
            "url": url_for(
                "main.view_inspection",
                inspection_id=i.id
            )
        })

    # Deviation
    deviations = Deviation.query.filter(
        Deviation.company_id == current_user.company_id,
        Deviation.deviation_number.ilike(f"%{q}%")
    ).limit(5)

    for d in deviations:
        results.append({
            "type": "Deviation",
            "title": d.deviation_number,
            "url": url_for(
                "main.view_deviation",
                deviation_id=d.id
            )
        })

    # Customer
    customers = Customer.query.filter(
        Customer.company_id == current_user.company_id,
        Customer.company_name.ilike(f"%{q}%")
    ).limit(5)

    for c in customers:
        results.append({
            "type": "Customer",
            "title": c.company_name,
            "url": url_for(
                "main.edit_customer",
                customer_id=c.id
            )
        })

    return jsonify(results)




