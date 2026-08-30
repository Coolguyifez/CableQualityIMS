"""
Role-based permissions for CableQIMS
"""


ROLE_PERMISSIONS = {

    # ==================================================
    # SYSTEM ADMINISTRATOR
    # ==================================================
    "System Administrator": {

        "manage_companies",

        "manage_users",

        "manage_customers",

        "manage_cable_types",

        "manage_production_lines",

        "manage_batches",

        "manage_inspections",

        "manage_specifications",

        "manage_quality_metrics",

        "manage_deviations",

        "manage_capa",

        "manage_notifications",

        "view_reports",

        "view_audit"

    },

    # ==================================================
    # COMPANY ADMINISTRATOR
    # ==================================================
    "Company Administrator": {


        "manage_users",

        "manage_customers",

        "manage_cable_types",

        "manage_production_lines",

        "manage_batches",

        "manage_inspections",

        "manage_specifications",

        "manage_quality_metrics",

        "manage_deviations",

        "manage_capa",

        "manage_notifications",

        "view_reports"

    },

    # ==================================================
    # QUALITY MANAGER
    # ==================================================
    "Quality Manager": {

        "manage_customers",

        "manage_batches",

        "manage_inspections",

        "manage_specifications",

        "manage_quality_metrics",

        "manage_deviations",

        "manage_capa",

        "view_reports",
        
        "manage_notifications"

    },

    # ==================================================
    # QUALITY INSPECTOR
    # ==================================================
    "Quality Inspector": {

        "manage_inspections",

        "manage_quality_metrics",

        "manage_deviations",
        
        "manage_notifications"


    },

    # ==================================================
    # PRODUCTION SUPERVISOR
    # ==================================================
    "Production Supervisor": {

        "manage_batches",

        "manage_production_lines",

        "manage_inspections",

        "manage_deviations",
        
        "manage_capa",
        
        "manage_notifications"

    },

    # ==================================================
    # PRODUCTION OPERATOR
    # ==================================================
    "Production Operator": {

        "manage_batches",
        
        "manage_notifications"

    },

    # ==================================================
    # VIEWER
    # ==================================================
    "Viewer": {

        "view_dashboard"

    }

}
