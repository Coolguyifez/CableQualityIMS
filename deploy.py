from flask_migrate import upgrade
from app import create_app
from app.extensions import db
from app.models import Company, User

app = create_app()

with app.app_context():

    # Run database migrations
    upgrade()

    print("Database migrations completed successfully.")

    # Create system company
    company = Company.query.filter_by(
        company_code="SYS"
    ).first()

    if not company:

        company = Company(
            company_name="CableQIMS",
            company_code="SYS",
            email="admin@cableqims.com",
            is_active=True
        )

        db.session.add(company)
        db.session.commit()

        print("Platform company created.")

    else:

        print("Platform company already exists.")

    # Create system administrator
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

    else:

        print("System Administrator already exists.")
