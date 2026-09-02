from sqlalchemy import func, extract

from flask_login import current_user

from app.extensions import db

from datetime import date, timedelta

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

def inspection_chart_by_period(company_id, period="monthly"):

    results = (
        db.session.query(
            Inspection.inspection_date
        )
        .filter(
            Inspection.company_id == company_id,
            Inspection.inspection_date.isnot(None)
        )
        .order_by(
            Inspection.inspection_date
        )
        .all()
    )

    period_counts = {}

    for (inspection_date,) in results:

        # Convert datetime to date if necessary
        if hasattr(inspection_date, "date"):
            inspection_date = inspection_date.date()

        # Daily
        if period == "daily":

            period_key = inspection_date

        # Weekly
        elif period == "weekly":

            # Monday is the beginning of the week
            period_key = (
                inspection_date
                - timedelta(
                    days=inspection_date.weekday()
                )
            )

        # Monthly
        else:

            period_key = (
                inspection_date.year,
                inspection_date.month
            )

        period_counts[period_key] = (
            period_counts.get(period_key, 0) + 1
        )

    labels = []
    data = []

    for period_key, count in period_counts.items():

        # Daily labels
        if period == "daily":

            labels.append(
                period_key.strftime("%d %b %Y")
            )

        # Weekly labels
        elif period == "weekly":

            week_end = (
                period_key
                + timedelta(days=6)
            )

            labels.append(
                f"{period_key.strftime('%d %b')} - "
                f"{week_end.strftime('%d %b %Y')}"
            )

        # Monthly labels
        else:

            year, month = period_key

            month_date = date(
                year,
                month,
                1
            )

            labels.append(
                month_date.strftime("%b %Y")
            )

        data.append(count)

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
        
        CAPA.due_date.isnot(None),
        
        CAPA.due_date <= date.today()

    ).count()

def todays_activities(company_id):

    return AuditLog.query.filter(

        AuditLog.company_id == company_id,

        func.date(

            AuditLog.created_at

        ) == date.today()

    ).count()
