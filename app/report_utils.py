from io import BytesIO

from flask import (
    request,
    send_file
)
from sqlalchemy import func, extract

from datetime import date

from openpyxl import Workbook

from openpyxl.styles import (
    Font,
    PatternFill
)

from app.extensions import db

from reportlab.lib.pagesizes import landscape, A4

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)

from reportlab.lib import colors

from reportlab.lib.styles import (
    getSampleStyleSheet
)

from reportlab.lib.enums import (
    TA_CENTER
)

from reportlab.lib.units import inch

from sqlalchemy.orm import joinedload

from .models import (
    Inspection,
    Deviation,
    CableBatch,
    Customer,
    CableType,
    ProductionLine,
    CAPA,
    QualityMetric,
    User,
    AuditLog

)

def get_filtered_inspection_query(company_id):

    query = Inspection.query.options(

        joinedload(
            Inspection.batch
        ).joinedload(
            CableBatch.customer
        ),

        joinedload(
            Inspection.batch
        ).joinedload(
            CableBatch.cable_type
        ),

        joinedload(
            Inspection.batch
        ).joinedload(
            CableBatch.production_line
        )

    ).filter(

        Inspection.company_id == company_id

    )

    date_from = request.args.get(
        "date_from"
    )

    date_to = request.args.get(
        "date_to"
    )

    inspector = request.args.get(
        "inspector"
    )

    status = request.args.get(
        "status"
    )

    customer = request.args.get(
        "customer"
    )

    cable_type = request.args.get(
        "cable_type"
    )

    production_line = request.args.get(
        "production_line"
    )

    batch_number = request.args.get(
        "batch_number"
    )

    if date_from:

        query = query.filter(

            Inspection.inspection_date >= date_from

        )

    if date_to:

        query = query.filter(

            Inspection.inspection_date <= date_to

        )

    if inspector:

        query = query.filter(

            Inspection.inspector.ilike(

                f"%{inspector}%"

            )

        )

    if status:

        query = query.filter(

            Inspection.overall_result == status

        )

    if customer:

        query = query.join(

            Inspection.batch

        ).join(

            CableBatch.customer

        ).filter(

            Customer.company_name.ilike(

                f"%{customer}%"

            )

        )

    if cable_type:

        query = query.join(

            Inspection.batch

        ).join(

            CableBatch.cable_type

        ).filter(

            CableType.name.ilike(

                f"%{cable_type}%"

            )

        )

    if production_line:

        query = query.join(

            Inspection.batch

        ).join(

            CableBatch.production_line

        ).filter(

            ProductionLine.line_name.ilike(

                f"%{production_line}%"

            )

        )

    if batch_number:

        query = query.join(

            Inspection.batch

        ).filter(

            CableBatch.batch_number.ilike(

                f"%{batch_number}%"

            )

        )

    return query

def apply_inspection_sort(query):

    sort = request.args.get(

        "sort",

        "inspection_date"

    )

    direction = request.args.get(

        "direction",

        "desc"

    )

    sort_columns = {

        "inspection_number": Inspection.inspection_number,

        "inspection_date": Inspection.inspection_date,

        "inspector": Inspection.inspector,

        "result": Inspection.overall_result

    }

    sort_column = sort_columns.get(

        sort,

        Inspection.inspection_date

    )

    if direction == "asc":

        query = query.order_by(

            sort_column.asc()

        )

    else:

        query = query.order_by(

            sort_column.desc()

        )

    return query

def paginate_query(

        query,

        per_page=20

):

    page = request.args.get(

        "page",

        1,

        type=int

    )

    pagination = query.paginate(

        page=page,

        per_page=per_page,

        error_out=False

    )

    return pagination


def get_inspection_statistics(query):

    total = query.count()

    passed = query.filter(

        Inspection.overall_result == "Pass"

    ).count()

    failed = query.filter(

        Inspection.overall_result == "Fail"

    ).count()

    pending = query.filter(

        Inspection.overall_result == "Pending"

    ).count()

    pass_rate = round(

        (passed / total) * 100,

        1

    ) if total else 0

    return {

        "total": total,

        "passed": passed,

        "failed": failed,

        "pending": pending,

        "pass_rate": pass_rate

    }

def export_excel(

        title,

        headers,

        rows,

        filename

):

    workbook = Workbook()

    worksheet = workbook.active

    worksheet.title = title

    header_fill = PatternFill(

        start_color="1F4E78",

        end_color="1F4E78",

        fill_type="solid"

    )

    header_font = Font(

        bold=True,

        color="FFFFFF"

    )

    # Write headers
    for column, header in enumerate(headers, start=1):

        cell = worksheet.cell(

            row=1,

            column=column

        )

        cell.value = header

        cell.fill = header_fill

        cell.font = header_font

    # Write rows
    current_row = 2

    for row in rows:

        for column, value in enumerate(row, start=1):

            worksheet.cell(

                row=current_row,

                column=column

            ).value = value

        current_row += 1

    # Auto-fit columns
    for column_cells in worksheet.columns:

        max_length = 0

        column_letter = column_cells[0].column_letter

        for cell in column_cells:

            try:

                if cell.value:

                    max_length = max(

                        max_length,

                        len(str(cell.value))

                    )

            except Exception:

                pass

        worksheet.column_dimensions[

            column_letter

        ].width = max_length + 5

    output = BytesIO()

    workbook.save(output)

    output.seek(0)

    return send_file(

        output,

        as_attachment=True,

        download_name=filename,

        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )

def export_pdf(

        title,

        headers,

        rows,

        filename

):

    buffer = BytesIO()

    document = SimpleDocTemplate(

        buffer,

        pagesize=landscape(A4),

        rightMargin=20,

        leftMargin=20,

        topMargin=20,

        bottomMargin=20

    )

    styles = getSampleStyleSheet()

    title_style = styles["Heading1"]

    title_style.alignment = TA_CENTER

    elements = []
    elements.append(

        Paragraph(

            f"<b>{title}</b>",

            title_style

        )

    )

    elements.append(

        Spacer(

            1,

            0.30 * inch

        )

    )
    table_data = [headers]

    for row in rows:

        table_data.append(row)

    table = Table(table_data, repeatRows= 1)
    table.setStyle(

        TableStyle([

            (

                "BACKGROUND",

                (0, 0),

                (-1, 0),

                colors.HexColor("#1E3A8A")

            ),

            (

                "TEXTCOLOR",

                (0, 0),

                (-1, 0),

                colors.white

            ),

            (

                "FONTNAME",

                (0, 0),

                (-1, 0),

                "Helvetica-Bold"

            ),

            (

                "FONTSIZE",

                (0, 0),

                (-1, -1),

                7

            ),

            (

                "GRID",

                (0, 0),

                (-1, -1),

                0.5,

                colors.grey

            ),

            (

                "BACKGROUND",

                (0, 1),

                (-1, -1),

                colors.whitesmoke

            ),

            (

                "ALIGN",

                (0, 0),

                (-1, -1),

                "CENTER"

            ),

            (

                "BOTTOMPADDING",

                (0, 0),

                (-1, 0),

                8

            )

        ])

    )

    elements.append(

        table

    )

    document.build(

        elements

    )

    buffer.seek(0)

    return send_file(

        buffer,

        as_attachment=True,

        download_name=filename,

        mimetype="application/pdf"

    )

#############################################################
# Generic Helpers
#############################################################

def build_rows(

        objects,

        columns

):

    rows = []

    for obj in objects:

        row = []

        for column in columns:

            value = obj

            for attr in column.split("."):

                value = getattr(

                    value,

                    attr,

                    ""

                )

            if hasattr(

                value,

                "strftime"

            ):

                value = value.strftime(

                    "%d-%m-%Y"

                )

            row.append(value)

        rows.append(row)

    return rows

def get_result_chart_data(query):

    passed = query.filter(

        Inspection.overall_result == "Pass"

    ).count()

    failed = query.filter(

        Inspection.overall_result == "Fail"

    ).count()

    pending = query.filter(

        Inspection.overall_result == "Pending"

    ).count()

    return {

        "labels": [

            "Pass",

            "Fail",

            "Pending"

        ],

        "values": [

            passed,

            failed,

            pending

        ]

    }


def get_monthly_trend(company_id):

    results = (
        db.session.query(
            Inspection.inspection_date,
            func.count(Inspection.id)
        )
        .filter(
            Inspection.company_id == company_id
        )
        .group_by(
            Inspection.inspection_date
        )
        .order_by(
            Inspection.inspection_date
        )
        .all()
    )

    labels = [
        date.strftime("%d %b %Y")
        for date, _ in results
    ]

    data = [
        count
        for _, count in results
    ]

    return {
        "labels": labels,
        "data": data
    }
def get_production_line_chart(company_id):

    results = (

        db.session.query(

            ProductionLine.line_name,

            func.count(

                Inspection.id

            )

        )

        .join(

            CableBatch,

            CableBatch.production_line_id == ProductionLine.id

        )

        .join(

            Inspection,

            Inspection.batch_id == CableBatch.id

        )

        .filter(

            Inspection.company_id == company_id

        )

        .group_by(

            ProductionLine.line_name

        )

        .all()

    )

    return {

        "labels":[

            row[0]

            for row in results

        ],

        "values":[

            row[1]

            for row in results

        ]

    }

def get_cable_type_chart(company_id):

    results = (

        db.session.query(

            CableType.name,

            func.count(

                Inspection.id

            )

        )

        .join(

            CableBatch,

            CableBatch.cable_type_id == CableType.id

        )

        .join(

            Inspection,

            Inspection.batch_id == CableBatch.id

        )

        .filter(

            Inspection.company_id == company_id

        )

        .group_by(

            CableType.name

        )

        .all()

    )

    return {

        "labels":[

            row[0]

            for row in results

        ],

        "values":[

            row[1]

            for row in results

        ]

    }

def get_filtered_deviation_query(company_id):

    query = Deviation.query.filter(

        Deviation.company_id == company_id

    )

    if request.args.get("status"):

        query = query.filter(

            Deviation.status == request.args.get("status")

        )

    if request.args.get("severity"):

        query = query.filter(

            Deviation.severity == request.args.get("severity")

        )

    if request.args.get("reported_by"):

        query = query.filter(

            Deviation.reported_by.ilike(

                f"%{request.args.get('reported_by')}%"

            )

        )

    if request.args.get("date_from"):

        query = query.filter(

            Deviation.created_at >= request.args.get("date_from")

        )

    if request.args.get("date_to"):

        query = query.filter(

            Deviation.created_at <= request.args.get("date_to")

        )

    return query


def get_deviation_statistics(query):

    total = query.count()

    open_count = query.filter(

        Deviation.status == "Open"

    ).count()

    progress = query.filter(

        Deviation.status == "In Progress"

    ).count()

    closed = query.filter(

        Deviation.status == "Closed"

    ).count()

    critical = query.filter(

        Deviation.severity == "Critical"

    ).count()

    return {

        "total": total,

        "open": open_count,

        "progress": progress,

        "closed": closed,

        "critical": critical

    }


def get_deviation_chart(query):

    open_count = query.filter(

        Deviation.status == "Open"

    ).count()

    progress = query.filter(

        Deviation.status == "In Progress"

    ).count()

    closed = query.filter(

        Deviation.status == "Closed"

    ).count()

    return {

        "labels": [

            "Open",

            "In Progress",

            "Closed"

        ],

        "values": [

            open_count,

            progress,

            closed

        ]

    }

def get_severity_chart(query):

    minor = query.filter(

        Deviation.severity == "Minor"

    ).count()

    major = query.filter(

        Deviation.severity == "Major"

    ).count()

    critical = query.filter(

        Deviation.severity == "Critical"

    ).count()

    return {

        "labels": [

            "Minor",

            "Major",

            "Critical"

        ],

        "values": [

            minor,

            major,

            critical

        ]

    }

def apply_deviation_sort(query):

    sort = request.args.get(

        "sort",

        "reported_date"

    )

    direction = request.args.get(

        "direction",

        "desc"

    )

    columns = {

        "deviation_number": Deviation.deviation_number,

        "severity": Deviation.severity,

        "status": Deviation.status,

        "reported_by": Deviation.reported_by,

        "reported_date": Deviation.reported_date,

        "closed_date": Deviation.closed_date

    }

    column = columns.get(

        sort,

        Deviation.reported_date

    )

    if direction == "asc":

        query = query.order_by(

            column.asc()

        )

    else:

        query = query.order_by(

            column.desc()

        )

    return query


def get_filtered_capa_query(company_id):

    query = CAPA.query.filter(

        CAPA.company_id == company_id

    )

    if request.args.get("status"):

        query = query.filter(

            CAPA.status == request.args.get("status")

        )

    if request.args.get("effectiveness"):

        query = query.filter(

            CAPA.effectiveness == request.args.get("effectiveness")

        )

    if request.args.get("assigned_to"):

        query = query.filter(

            CAPA.assigned_to.ilike(

                f"%{request.args.get('assigned_to')}%"

            )

        )

    if request.args.get("date_from"):

        query = query.filter(

            CAPA.due_date >= request.args.get("date_from")

        )

    if request.args.get("date_to"):

        query = query.filter(

            CAPA.due_date <= request.args.get("date_to")

        )

    return query

def apply_capa_sort(query):

    sort = request.args.get(

        "sort",

        "due_date"

    )

    direction = request.args.get(

        "direction",

        "desc"

    )

    columns = {

        "id": CAPA.id,

        "assigned_to": CAPA.assigned_to,

        "status": CAPA.status,

        "effectiveness": CAPA.effectiveness,

        "due_date": CAPA.due_date,

        "completion_date": CAPA.completion_date

    }

    column = columns.get(

        sort,

        CAPA.due_date

    )

    if direction == "asc":

        query = query.order_by(

            column.asc()

        )

    else:

        query = query.order_by(

            column.desc()

        )

    return query

def get_capa_status_chart(query):

    return {

        "labels": [

            "Open",

            "In Progress",

            "Completed",

            "Overdue",

            "Closed"

        ],

        "data": [

            query.filter(

                CAPA.status == "Open"

            ).count(),

            query.filter(

                CAPA.status == "In Progress"

            ).count(),

            query.filter(

                CAPA.status == "Completed"

            ).count(),

            query.filter(

                CAPA.status == "Overdue"

            ).count(),

            query.filter(

                CAPA.status == "Closed"

            ).count()

        ]

    }

def get_capa_statistics(query):

    total = query.count()

    open_count = query.filter(
        CAPA.status == "Open"
    ).count()

    progress = query.filter(
        CAPA.status == "In Progress"
    ).count()

    completed = query.filter(
        CAPA.status == "Completed"
    ).count()

    closed = query.filter(
        CAPA.status == "Closed"
    ).count()

    overdue = query.filter(

        CAPA.due_date < date.today(),

        CAPA.status != "Closed"

    ).count()

    return {
        "total": total,
        "open": open_count,
        "progress": progress,
        "completed": completed,
        "closed": closed,
        "overdue": overdue
    }

def get_capa_effectiveness_chart(query):

    return {

        "labels": [

            "Pending",

            "Effective",

            "Not Effective"

        ],

        "data": [

            query.filter(

                CAPA.effectiveness == "Pending"

            ).count(),

            query.filter(

                CAPA.effectiveness == "Effective"

            ).count(),

            query.filter(

                CAPA.effectiveness == "Not Effective"

            ).count()

        ]

    }


def get_filtered_quality_metric_query(company_id):

    query = QualityMetric.query.filter(

        QualityMetric.company_id == company_id

    )

    if request.args.get("result"):

        query = query.filter(

            QualityMetric.result == request.args.get("result")

        )

    if request.args.get("inspection"):

        query = query.join(

            Inspection

        ).filter(

            Inspection.inspection_number.ilike(

                f"%{request.args.get('inspection')}%"

            )

        )

    if request.args.get("date_from"):

        query = query.join(

            Inspection

        ).filter(

            Inspection.inspection_date >= request.args.get("date_from")

        )

    if request.args.get("date_to"):

        query = query.join(

            Inspection

        ).filter(

            Inspection.inspection_date <= request.args.get("date_to")

        )

    return query

def apply_quality_metric_sort(query):

    sort = request.args.get(

        "sort",

        "result"

    )

    direction = request.args.get(

        "direction",

        "asc"

    )

    columns = {

        "measured_value": QualityMetric.measured_value,

        "result": QualityMetric.result

    }

    column = columns.get(

        sort,

        QualityMetric.result

    )

    if direction == "asc":

        query = query.order_by(

            column.asc()

        )

    else:

        query = query.order_by(

            column.desc()

        )

    return query

def get_quality_metric_statistics(query):

    total = query.count()

    passed = query.filter(

        QualityMetric.result == "Pass"

    ).count()

    failed = query.filter(

        QualityMetric.result == "Fail"

    ).count()

    return {

        "total": total,

        "passed": passed,

        "failed": failed

    }

def get_quality_metric_chart(query):

    return {

        "labels":[

            "Pass",

            "Fail"

        ],

        "values":[

            query.filter(

                QualityMetric.result=="Pass"

            ).count(),

            query.filter(

                QualityMetric.result=="Fail"

            ).count()

        ]

    }

def get_filtered_production_query(company_id):

    query = CableBatch.query.filter(

        CableBatch.company_id == company_id

    )

    if request.args.get("status"):

        query = query.filter(

            CableBatch.status == request.args.get("status")

        )

    if request.args.get("customer"):

        query = query.join(

            Customer

        ).filter(

            Customer.company_name.ilike(

                f"%{request.args.get('customer')}%"

            )

        )

    if request.args.get("production_line"):

        query = query.join(

            ProductionLine

        ).filter(

            ProductionLine.line_name == request.args.get(

                "production_line"

            )

        )

    if request.args.get("date_from"):

        query = query.filter(

            CableBatch.production_date >= request.args.get(

                "date_from"

            )

        )

    if request.args.get("date_to"):

        query = query.filter(

            CableBatch.production_date <= request.args.get(

                "date_to"

            )

        )

    return query

def apply_production_sort(query):

    sort = request.args.get(

        "sort",

        "production_date"

    )

    direction = request.args.get(

        "direction",

        "desc"

    )

    columns = {

        "batch_number": CableBatch.batch_number,

        "drum_number": CableBatch.drum_number,

        "production_date": CableBatch.production_date,

        "status": CableBatch.status,

        "cable_length": CableBatch.cable_length

    }

    column = columns.get(

        sort,

        CableBatch.production_date

    )

    if direction == "asc":

        query = query.order_by(

            column.asc()

        )

    else:

        query = query.order_by(

            column.desc()

        )

    return query

def get_production_statistics(query):

    total = query.count()

    pending = query.filter(

        CableBatch.status == "Pending"

    ).count()

    completed = query.filter(

        CableBatch.status == "Completed"

    ).count()

    rejected = query.filter(

        CableBatch.status == "Rejected"

    ).count()

    total_length = sum(

        batch.cable_length

        for batch in query.all()

    )

    return {

        "total": total,

        "pending": pending,

        "completed": completed,

        "rejected": rejected,

        "total_length": total_length

    }

def get_production_status_chart(query):

    return {

        "labels":[

            "Pending",

            "Completed",

            "Rejected"

        ],

        "values":[

            query.filter(

                CableBatch.status=="Pending"

            ).count(),

            query.filter(

                CableBatch.status=="Completed"

            ).count(),

            query.filter(

                CableBatch.status=="Rejected"

            ).count()

        ]

    }

def get_filtered_customer_query(company_id):

    query = Customer.query.filter(

        Customer.company_id == company_id

    )

    if request.args.get("company_name"):

        query = query.filter(

            Customer.company_name.ilike(

                f"%{request.args.get('company_name')}%"

            )

        )

    if request.args.get("contact_person"):

        query = query.filter(

            Customer.contact_person.ilike(

                f"%{request.args.get('contact_person')}%"

            )

        )

    if request.args.get("email"):

        query = query.filter(

            Customer.email.ilike(

                f"%{request.args.get('email')}%"

            )

        )

    return query

def apply_customer_sort(query):

    sort = request.args.get(

        "sort",

        "company_name"

    )

    direction = request.args.get(

        "direction",

        "asc"

    )

    columns = {

        "company_name": Customer.company_name,

        "contact_person": Customer.contact_person,

        "email": Customer.email,

        "phone": Customer.phone,

        "created_at": Customer.created_at

    }

    column = columns.get(

        sort,

        Customer.company_name

    )

    if direction == "asc":

        query = query.order_by(

            column.asc()

        )

    else:

        query = query.order_by(

            column.desc()

        )

    return query


def get_customer_request_chart(company_id):
    """
    Number of accepted cable requests per customer.
    Rejected batches are excluded.
    """

    results = (
        db.session.query(
            Customer.company_name,
            func.count(CableBatch.id)
        )
        .join(
            CableBatch,
            CableBatch.customer_id == Customer.id
        )
        .filter(
            Customer.company_id == company_id,
            CableBatch.status != "Rejected"
        )
        .group_by(
            Customer.id,
            Customer.company_name
        )
        .order_by(
            func.count(CableBatch.id).desc()
        )
        .all()
    )

    return {
        "labels": [r[0] for r in results],
        "values": [r[1] for r in results]
    }

def get_customer_statistics(query):

    total = query.count()

    with_email = query.filter(

        Customer.email.isnot(None),

        Customer.email != ""

    ).count()

    with_phone = query.filter(

        Customer.phone.isnot(None),

        Customer.phone != ""

    ).count()

    return {

        "total": total,

        "with_email": with_email,

        "with_phone": with_phone

    }

def get_filtered_user_query(company_id):

    query = User.query.filter(

        User.company_id == company_id

    )

    if request.args.get("full_name"):

        query = query.filter(

            User.full_name.ilike(

                f"%{request.args.get('full_name')}%"

            )

        )

    if request.args.get("email"):

        query = query.filter(

            User.email.ilike(

                f"%{request.args.get('email')}%"

            )

        )

    if request.args.get("role"):

        query = query.filter(

            User.role == request.args.get(

                "role"

            )

        )

    if request.args.get("active"):

        active = request.args.get("active") == "true"

        query = query.filter(

            User.is_active == active

        )

    return query

def apply_user_sort(query):

    sort = request.args.get(

        "sort",

        "full_name"

    )

    direction = request.args.get(

        "direction",

        "asc"

    )

    columns = {

        "full_name": User.full_name,

        "username": User.username,

        "email": User.email,

        "role": User.role,

        "created_at": User.created_at

    }

    column = columns.get(

        sort,

        User.full_name

    )

    if direction == "asc":

        query = query.order_by(

            column.asc()

        )

    else:

        query = query.order_by(

            column.desc()

        )

    return query

def get_user_statistics(query):

    total = query.count()

    active = query.filter(

        User.is_active == True

    ).count()

    inactive = query.filter(

        User.is_active == False

    ).count()

    admins = query.filter(

        User.role == "Admin"

    ).count()

    return {

        "total": total,

        "active": active,

        "inactive": inactive,

        "admins": admins

    }

def get_user_status_chart(query):

    return {

        "labels":[

            "Active",

            "Inactive"

        ],

        "values":[

            query.filter(

                User.is_active == True

            ).count(),

            query.filter(

                User.is_active == False

            ).count()

        ]

    }


def get_filtered_audit_query(company_id):

    query = AuditLog.query.filter(

        AuditLog.company_id == company_id

    )

    if request.args.get("module"):

        query = query.filter(

            AuditLog.module.ilike(

                f"%{request.args.get('module')}%"

            )

        )

    if request.args.get("action"):

        query = query.filter(

            AuditLog.action.ilike(

                f"%{request.args.get('action')}%"

            )

        )

    if request.args.get("user"):

        query = query.join(

            User

        ).filter(

            User.full_name.ilike(

                f"%{request.args.get('user')}%"

            )

        )

    if request.args.get("date_from"):

        query = query.filter(

            AuditLog.created_at >= request.args.get(

                "date_from"

            )

        )

    if request.args.get("date_to"):

        query = query.filter(

            AuditLog.created_at <= request.args.get(

                "date_to"

            )

        )

    return query


def apply_audit_sort(query):

    sort = request.args.get(

        "sort",

        "created_at"

    )

    direction = request.args.get(

        "direction",

        "desc"

    )

    columns = {

        "module": AuditLog.module,

        "action": AuditLog.action,

        "created_at": AuditLog.created_at

    }

    column = columns.get(

        sort,

        AuditLog.created_at

    )

    if direction == "asc":

        query = query.order_by(

            column.asc()

        )

    else:

        query = query.order_by(

            column.desc()

        )

    return query

def get_audit_statistics(query):

    total = query.count()

    modules = query.with_entities(

        AuditLog.module

    ).distinct().count()

    actions = query.with_entities(

        AuditLog.action

    ).distinct().count()

    users = query.with_entities(

        AuditLog.user_id

    ).distinct().count()

    return {

        "total": total,

        "modules": modules,

        "actions": actions,

        "users": users

    }

def get_audit_chart(query):

    data = query.all()

    counts = {}

    for log in data:

        counts[log.module] = (

            counts.get(

                log.module,

                0

            ) + 1

        )

    return {

        "labels": list(

            counts.keys()

        ),

        "data": list(

            counts.values()

        )

    }


