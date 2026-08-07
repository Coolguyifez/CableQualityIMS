from datetime import datetime
from flask_login import UserMixin
from .extensions import login_manager
from .extensions import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
        default=1
    )

    full_name = db.Column(
        db.String(120),
        nullable=False
    )

    username = db.Column(
        db.String(50),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(50),
        default="Quality Inspector",
        nullable=False
    )

    theme = db.Column(
        db.String(20),
        nullable=False,
        default="system"
    )

    notification_enabled = db.Column(
        db.Boolean,
        default=True
    )

    failure_sound = db.Column(
        db.Boolean,
        default=True
    )

    inspection_notification = db.Column(
        db.Boolean,
        default=True
    )

    deviation_notification = db.Column(
        db.Boolean,
        default=True
    )

    capa_notification = db.Column(
        db.Boolean,
        default=True
    )

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    company = db.relationship(
        "Company",
        back_populates="users"
    )

    # -------------------------
    # Password Methods
    # -------------------------

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(
            self.password_hash,
            password
        )

    @property
    def company_name(self):
        return self.company.company_name

    __table_args__ = (

        db.UniqueConstraint(

            "company_id",

            "username",

            name="uq_company_username"

        ),

        db.UniqueConstraint(

            "company_id",

            "email",

            name="uq_company_email"

        ),

    )

    def __repr__(self):
        return f"<User {self.username}>"

class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    company_name = db.Column(
        db.String(150),
        unique=True,
        nullable=False
    )

    company_code = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    address = db.Column(
        db.Text
    )


    email = db.Column(
        db.String(120)
    )

    phone = db.Column(
        db.String(30)
    )

    logo = db.Column(
        db.String(200)
    )

    is_active = db.Column(
        db.Boolean,
        default=True
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    users = db.relationship(
        "User",
        back_populates="company"
    )

    def __repr__(self):
        return self.company_name

class CableBatch(db.Model):
    __tablename__ = "cable_batches"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
        default=1
    )

    batch_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    drum_number = db.Column(
        db.String(50),
        nullable=False
    )

    drain_wire_type = db.Column(
        db.String(5),
        nullable=False
    )

    specialty = db.Column(
        db.String(5),
        nullable=False
    )

    water_barrier = db.Column(
        db.String(5),
        nullable=False
    )

    outer_sheath_colour = db.Column(
        db.String(10),
        nullable=False
    )

    cable_code = db.Column(
        db.String(50),
        nullable=False
    )

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        nullable=False
    )

    cable_type_id = db.Column(
        db.Integer,
        db.ForeignKey("cable_types.id"),
        nullable=False
    )

    production_line_id = db.Column(
        db.Integer,
        db.ForeignKey("production_lines.id"),
        nullable=False
    )

    production_date = db.Column(
        db.Date,
        nullable=False
    )

    cable_length = db.Column(
        db.Float,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="Pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    company = db.relationship(
        "Company",
        backref="batches"
    )

    customer = db.relationship(
        "Customer",
        back_populates="batches"
    )

    cable_type = db.relationship(
        "CableType",
        back_populates="batches"
    )

    production_line = db.relationship(
        "ProductionLine",
        back_populates="batches"
    )

    inspections = db.relationship(
        "Inspection",
        back_populates="batch",
        cascade="all, delete-orphan"
    )



    def __repr__(self):
        return f"<Batch {self.batch_number}>"

class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
        default=1
    )
    company_name = db.Column(db.String(150), nullable=False)

    contact_person = db.Column(db.String(100))

    email = db.Column(db.String(120))

    phone = db.Column(db.String(30))

    address = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    company = db.relationship(
        "Company",
        backref="customers"
    )
    batches = db.relationship(
        "CableBatch",
        back_populates="customer",
        cascade="all, delete"
    )


    def __repr__(self):
        return f"<Customer {self.company_name}>"


class ProductionLine(db.Model):
    __tablename__ = "production_lines"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
        default=1
    )

    line_name = db.Column(
        db.String(100),
        nullable=False
    )

    location = db.Column(
        db.String(100),
        nullable=False
    )

    supervisor = db.Column(
        db.String(100),
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False,
        default="Active"
    )

    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    company = db.relationship(
        "Company",
        backref="production_lines"
    )

    batches = db.relationship(
        "CableBatch",
        back_populates="production_line",
        cascade="all, delete"
    )

    def __repr__(self):
        return f"<ProductionLine {self.line_name}>"


class CableType(db.Model):
    __tablename__ = "cable_types"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
        default=1
    )

    # ----------------------------------
    # Basic Description
    # ----------------------------------

    name = db.Column(
        db.String(150),
        nullable=False
    )

    pair_count = db.Column(
        db.String(10),      # 1P,2P,5P,8P...
        nullable=False
    )

    conductor_size = db.Column(
        db.String(20),      # 1.0mm,1.5mm...
        nullable=False
    )

    voltage_rating = db.Column(
        db.String(50),      #300/500V
        nullable=False
    )

    drain_configuration = db.Column(
        db.String(20),      #OS / IS-OS
        nullable=False
    )

    # ----------------------------------
    # Construction
    # ----------------------------------

    conductor_material = db.Column(
        db.String(50),      #CU(SOL) / CU(STRD)
        nullable=False
    )

    insulation_material = db.Column(
        db.String(50),      #XLPE/PVC
        nullable=False
    )

    fire_resistant_material = db.Column(
        db.String(30),      #MICA/NONE
        default="NONE"
    )

    inner_sheath_material = db.Column(
        db.String(30),      #PVC/LSZH
    )

    armour_type = db.Column(
        db.String(30),      #SWA/FLAT
    )

    outer_sheath_material = db.Column(
        db.String(30),      #PVC/LSZH
    )

    flame_retardant = db.Column(
        db.String(20),      #FR/NONE
        default="NONE"
    )

    application = db.Column(
        db.String(200)
    )

    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    company = db.relationship(
        "Company",
        backref="cable_types"
    )

    batches = db.relationship(
        "CableBatch",
        back_populates="cable_type",
        cascade="all, delete"
    )

    def __repr__(self):
        return f"<CableType {self.name}>"


class Inspection(db.Model):
    __tablename__ = "inspections"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
        default=1
    )

    inspection_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    batch_id = db.Column(
        db.Integer,
        db.ForeignKey("cable_batches.id"),
        nullable=False
    )

    inspector = db.Column(
        db.String(100),
        nullable=False
    )

    inspection_date = db.Column(
        db.Date,
        nullable=False
    )

    overall_result = db.Column(
        db.String(20),
        nullable=False,
        default="Pending"
    )

    remarks = db.Column(db.Text)

    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )


    company = db.relationship(
        "Company",
        backref="inspections"
    )

    batch = db.relationship(
        "CableBatch",
        back_populates="inspections"
    )

    quality_metrics = db.relationship(
        "QualityMetric",
        back_populates="inspection",
        cascade="all, delete-orphan"
    )



    def __repr__(self):
        return f"<Inspection {self.inspection_number}>"



class QualityMetric(db.Model):
    __tablename__ = "quality_metrics"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
        default=1
    )

    inspection_id = db.Column(
        db.Integer,
        db.ForeignKey("inspections.id"),
        nullable=False
    )

    specification_id = db.Column(
        db.Integer,
        db.ForeignKey("quality_specifications.id"),
        nullable=False
    )

    measured_value = db.Column(
        db.String(100),
        nullable=False
    )

    result = db.Column(
        db.String(20),
        default="Pending"
    )

    company = db.relationship(
        "Company",
        backref="quality_metrics"
    )

    inspection = db.relationship(
        "Inspection",
        back_populates="quality_metrics"
    )

    deviations = db.relationship(
        "Deviation",
        back_populates="quality_metric",
        cascade="all, delete-orphan"
    )


    specification = db.relationship(
        "QualitySpecification"
    )



class QualitySpecification(db.Model):
    __tablename__ = "quality_specifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
        default=1
    )

    cable_type_id = db.Column(
        db.Integer,
        db.ForeignKey("cable_types.id"),
        nullable=False
    )

    # Example:
    # Conductor Design
    # DC Resistance
    # Spark Test
    metric_name = db.Column(
        db.String(150),
        nullable=False
    )

    # mm, %, Ω/km, m, kV...
    unit = db.Column(
        db.String(30),
        nullable=True
    )

    # Validation method
    # any
    # minimum
    # maximum
    # range
    # text
    validation_type = db.Column(
        db.String(20),
        nullable=False,
        default="range"
    )

    # Numeric Limits
    minimum_value = db.Column(
        db.Float,
        default=0
    )

    maximum_value = db.Column(
        db.Float,
        default=0
    )

    # Display requirement
    # e.g.
    # "1.78 ±0.02"
    # "22 (Min)"
    # "7.41 (Max)"
    requirement = db.Column(
        db.String(150),
        nullable=True
    )

    # Used only for text validation
    # Examples:
    # "Passed"
    # "Withstood"
    # "No Breakdown Shall Occur"
    expected_result = db.Column(
        db.String(200),
        nullable=True
    )

    # Optional help message
    non_conformance_message = db.Column(
        db.String(300),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=db.func.current_timestamp()
    )

    company = db.relationship(
        "Company",
        backref="quality_specifications"
    )

    cable_type = db.relationship(
        "CableType",
        backref="quality_specifications"
    )

    def __repr__(self):
        return f"<QualitySpecification {self.metric_name}>"


class Deviation(db.Model):
    __tablename__ = "deviations"

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
        default=1
    )

    deviation_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    inspection_id = db.Column(
        db.Integer,
        db.ForeignKey("inspections.id"),
        nullable=False
    )

    quality_metric_id = db.Column(
        db.Integer,
        db.ForeignKey("quality_metrics.id"),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    severity = db.Column(
        db.String(20),
        default="Minor"
    )

    root_cause = db.Column(
        db.Text
    )



    status = db.Column(
        db.String(20),
        default="Open"
    )

    reported_by = db.Column(
        db.String(100),
        nullable=False
    )

    reported_date = db.Column(
        db.Date,
        default=datetime.utcnow
    )

    closed_date = db.Column(
        db.Date
    )

    company = db.relationship(
        "Company",
        backref="deviations"
    )

    inspection = db.relationship(
        "Inspection",
        backref="deviations"
    )

    quality_metric = db.relationship(
        "QualityMetric",
        back_populates="deviations"
    )

    capa = db.relationship(
        "CAPA",
        back_populates="deviation",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Deviation {self.deviation_number}>"



class CAPA(db.Model):
    __tablename__ = "capa"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False,
        default=1
    )


    deviation_id = db.Column(
        db.Integer,
        db.ForeignKey("deviations.id"),
        nullable=False
    )

    corrective_action = db.Column(
        db.Text,
        nullable=False
    )

    preventive_action = db.Column(
        db.Text,
        nullable=False
    )

    assigned_to = db.Column(
        db.String(100),
        nullable=False
    )

    due_date = db.Column(
        db.Date
    )

    completion_date = db.Column(
        db.Date
    )

    effectiveness = db.Column(
        db.String(20),
        default="Pending"
    )

    status = db.Column(
        db.String(20),
        default="Open"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )


    company = db.relationship(
        "Company",
        backref="capas"
    )

    deviation = db.relationship(
        "Deviation",
        back_populates="capa"
    )

    def __repr__(self):
        return f"<CAPA {self.id}>"

class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id")
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    category = db.Column(
        db.String(50),
        default="General"
    )

    priority = db.Column(
        db.String(20),
        default="Normal"
    )

    link = db.Column(
        db.String(300)
    )

    is_read = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    company = db.relationship(
        "Company",
        backref="notifications"
    )

    user = db.relationship(
        "User",
        backref="notifications"
    )

    def __repr__(self):

        return f"<Notification {self.title}>"


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("companies.id"),
        nullable=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=True
    )

    module = db.Column(
        db.String(100),
        nullable=False
    )

    action = db.Column(
        db.String(100),
        nullable=False
    )

    description = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    company = db.relationship(
        "Company"
    )

    user = db.relationship(
        "User"
    )

    def __repr__(self):
        return f"<AuditLog {self.module} - {self.action}>"






