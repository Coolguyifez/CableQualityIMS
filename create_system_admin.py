from app import create_app
from app.extensions import db
from app.models import Company, User


app = create_app()


with app.app_context():

    # -----------------------------------------
    # Find or create platform company
    # -----------------------------------------

    company = Company.query.filter_by(
        company_code="SYS"
    ).first()

    if not company:

        company = Company(
            company_name="CableQIMS Platform",
            company_code="SYS",
            email="admin@cableqims.com",
            is_active=True
        )

        db.session.add(company)
        db.session.commit()

        print("Platform company created.")

    else:

        print("Platform company already exists.")

    # -----------------------------------------
    # Find or create system administrator
    # -----------------------------------------

    admin = User.query.filter_by(
        username="superadmin"
    ).first()

    if not admin:

        admin = User(
            company_id=company.id,
            full_name="System Administrator",
            username="superadmin",
            email="admin@cableqims.com",
            role="System Administrator",
            is_active=True
        )

        admin.set_password("Admin@123")

        db.session.add(admin)
        db.session.commit()

        print("System Administrator created.")

        print()
        print("====================================")
        print("SYSTEM ADMINISTRATOR")
        print("====================================")
        print("Username: superadmin")
        print("Password: Admin@123")
        print("====================================")
        print("IMPORTANT: Change this password immediately.")
        print("====================================")

    else:

        print("System Administrator already exists.")

