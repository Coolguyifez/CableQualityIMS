from sqlalchemy import func, extract

from flask_login import current_user

from app.extensions import db

from datetime import date

from .models import (

    Inspection,

    CAPA,

    Deviation,

    CableBatch,

    Customer,

    ProductionLine,

    CableType,

    User,

    AuditLog

)

def get_dashboard_statistics(company_id):

    total_inspections = Inspection.query.filter_by(

        company_id=company_id

    ).count()

    passed = Inspection.query.filter_by(

        company_id=company_id,

        overall_result="Pass"

    ).count()

    failed = Inspection.query.filter_by(

        company_id=company_id,

        overall_result="Fail"

    ).count()

    pending = Inspection.query.filter_by(

        company_id=company_id,

        overall_result="Pending"

    ).count()

    open_capa = CAPA.query.filter_by(

        company_id=company_id,

        status="Open"

    ).count()

    deviations = Deviation.query.filter_by(

        company_id=company_id

    ).count()

    users = User.query.filter_by(

        company_id=company_id

    ).count()

    batches = CableBatch.query.filter_by(

        company_id=company_id

    ).count()

    customers = Customer.query.filter_by(

        company_id=company_id

    ).count()

    lines = ProductionLine.query.filter_by(

        company_id=company_id

    ).count()

    cable_types = CableType.query.filter_by(

        company_id=company_id

    ).count()

    return {

        "inspections": total_inspections,

        "passed": passed,

        "failed": failed,

        "pending": pending,

        "open_capa": open_capa,

        "deviations": deviations,

        "users": users,

        "batches": batches,

        "customers": customers,

        "lines": lines,

        "cable_types": cable_types

    }

def inspection_chart(company_id):

    return {

        "labels":[

            "Pass",

            "Fail",

            "Pending"

        ],

        "data":[

            Inspection.query.filter_by(

                company_id=company_id,

                overall_result="Pass"

            ).count(),

            Inspection.query.filter_by(

                company_id=company_id,

                overall_result="Fail"

            ).count(),

            Inspection.query.filter_by(

                company_id=company_id,

                overall_result="Pending"

            ).count()

        ]

    }

def capa_chart(company_id):

    return {

        "labels":[

            "Open",

            "In Progress",

            "Completed",

            "Overdue",
    
            "Closed"

        ],

        "data":[

            CAPA.query.filter_by(

                company_id=company_id,

                status="Open"

            ).count(),

            CAPA.query.filter_by(

                company_id=company_id,

                status="In Progress"

            ).count(),

            CAPA.query.filter_by(

                company_id=company_id,

                status="Completed"

            ).count(),

            CAPA.query.filter_by(

                company_id=company_id,

                status="Overdue"

            ).count(),

            CAPA.query.filter_by(

                company_id=company_id,

                status="Closed"

            ).count()

        ]

    }

def deviation_chart(company_id):

    return {

        "labels":[

            "Minor",

            "Major",

            "Critical"

        ],

        "data":[

            Deviation.query.filter_by(

                company_id=company_id,

                severity="Minor"

            ).count(),

            Deviation.query.filter_by(

                company_id=company_id,

                severity="Major"

            ).count(),

            Deviation.query.filter_by(

                company_id=company_id,

                severity="Critical"

            ).count()

        ]

    }

def monthly_inspection_chart(company_id):

    results = (
        db.session.query(
            Inspection.inspection_date,
            func.count(Inspection.id).label("count")
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
        inspection_date.strftime("%d %b %Y")
        for inspection_date, _ in results
    ]

    data = [
        count
        for _, count in results
    ]

    return {
        "labels": labels,
        "data": data
    }

def production_line_chart(company_id):

    labels = []

    data = []

    lines = ProductionLine.query.filter_by(

        company_id=company_id

    ).all()

    for line in lines:

        labels.append(

            line.line_name

        )

        data.append(

            CableBatch.query.filter_by(

                company_id=company_id,

                production_line_id=line.id

            ).count()

        )

    return {

        "labels": labels,

        "data": data

    }

def recent_inspections(company_id, limit=5):

    return Inspection.query.filter_by(

        company_id=company_id

    ).order_by(

        Inspection.inspection_date.desc()

    ).limit(limit).all()

def recent_capas(company_id, limit=5):

    return CAPA.query.filter_by(

        company_id=company_id

    ).order_by(

        CAPA.created_at.desc()

    ).limit(limit).all()


def recent_audits(company_id, limit=10):

    return AuditLog.query.filter_by(

        company_id=company_id

    ).order_by(

        AuditLog.created_at.desc()

    ).limit(limit).all()

def pass_rate(company_id):

    total = Inspection.query.filter_by(

        company_id=company_id

    ).count()

    passed = Inspection.query.filter_by(

        company_id=company_id,

        overall_result="Pass"

    ).count()

    if total == 0:

        return 0

    return round(

        (passed / total) * 100,

        1

    )


def overdue_capas(company_id):

    return CAPA.query.filter(

        CAPA.company_id == company_id,

        CAPA.status != "Closed",

        CAPA.due_date < date.today()

    ).count()

def todays_activities(company_id):

    return AuditLog.query.filter(

        AuditLog.company_id == company_id,

        func.date(

            AuditLog.created_at

        ) == date.today()

    ).count()