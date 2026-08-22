from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, Email, Length, EqualTo, Optional
from wtforms import (
    StringField,
    PasswordField,
    BooleanField,
    SubmitField,
    SelectField,
    EmailField,
    FloatField,
    DateField,
    TextAreaField,

)

class UserForm(FlaskForm):

    full_name = StringField(
        "Full Name",
        validators=[DataRequired()]
    )

    username = StringField(
        "Username",
        validators=[DataRequired()]
    )

    email = StringField(
        "Email",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    password = PasswordField(
        "Password"
    )

    role = SelectField(
        "Role",
        choices=[
            ("Company Administrator",
             "Company Administrator"),

            ("Quality Manager",
             "Quality Manager"),

            ("Quality Inspector",
             "Quality Inspector"),

            ("Production Supervisor",
             "Production Supervisor"),

            ("Production Operator",
             "Production Operator"),

            ("Viewer",
             "Viewer")

        ]
    )

    is_active = BooleanField(
        "Active",
        default=True
    )

    submit = SubmitField(
        "Save User"
    )


class CompanyForm(FlaskForm):

    company_name = StringField(

        "Company Name",

        validators=[

            DataRequired(),

            Length(max=150)

        ]

    )

    company_code = StringField(

        "Company Code",

        validators=[

            DataRequired(),

            Length(max=20)

        ]

    )

    address = TextAreaField(

        "Address"

    )

    email = StringField(

        "Company Email",

        validators=[

            Optional(),

            Email()

        ]

    )

    phone = StringField(

        "Phone"

    )

    logo = StringField(

        "Logo URL"

    )

    admin_full_name = StringField(
        "Administrator Full Name",
        validators=[DataRequired()]
    )

    admin_username = StringField(
        "Administrator Username",
        validators=[DataRequired()]
    )

    admin_email = StringField(
        "Administrator Email",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    admin_password = PasswordField(
        "Temporary Password",
        validators=[DataRequired()]
    )

    is_active = BooleanField(

        "Active",

        default=True

    )

    submit = SubmitField(

        "Save Company"

    )


class LoginForm(FlaskForm):

    company_code = StringField(
        "Company Code",
        validators=[
            DataRequired()
        ]
    )

    username = StringField(
        "Username",
        validators=[
            DataRequired()
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired()
        ]
    )

    remember = BooleanField(
        "Remember Me"
    )

    submit = SubmitField(
        "Login"
    )

class CompanyRegistrationForm(FlaskForm):

    company_name = StringField(
        "Company Name",
        validators=[
            DataRequired(),
            Length(max=150)
        ]
    )

    company_code = StringField(
        "Company Code",
        validators=[
            DataRequired(),
            Length(max=20)
        ]
    )

    company_email = StringField(
        "Company Email",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    company_phone = StringField(
        "Company Phone",
        validators=[
            DataRequired()
        ]
    )

    company_address = TextAreaField(
        "Company Address",
        validators=[
            DataRequired()
        ]
    )

    admin_name = StringField(
        "Administrator Full Name",
        validators=[
            DataRequired()
        ]
    )

    username = StringField(
        "Username",
        validators=[
            DataRequired()
        ]
    )

    email = StringField(
        "Administrator Email",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters.")
        ]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo(
                "password",
                message="Passwords must match."
            )
        ]
    )

    submit = SubmitField(
        "Create Company"
    )

class ChangePasswordForm(FlaskForm):

    current_password = PasswordField(
        "Current Password",
        validators=[DataRequired()]
    )

    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=6)
        ]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("new_password")
        ]
    )

    submit = SubmitField(
        "Change Password"
    )

class CableBatchForm(FlaskForm):
#bash number is been  generated

    batch_number = StringField(
        "Batch Number",
        render_kw={"readonly": True}
    )

    cable_code = StringField(
        "Cable Code",
        render_kw={"readonly": True}
    )

    drum_number = StringField(
        "Drum Number",
        validators=[DataRequired()]
    )

    drain_wire_type = SelectField(
        "Drain Wire Type",
        choices=[
            ("P", "P"),
            ("R", "R"),
            ("S", "S"),
            ("N", "N"),
            ("V", "V")
        ],
        validators=[DataRequired()]
    )

    specialty = SelectField(
        "Specialty",
        choices=[
            ("A", "A"),
            ("B", "B")
        ],
        validators=[DataRequired()]
    )

    water_barrier = SelectField(
        "Water Barrier",
        choices=[
            ("R", "R"),
            ("C", "C")
        ],
        validators=[DataRequired()]
    )


    outer_sheath_colour = SelectField(
        "Outer Sheath Colour",
        choices=[
            ("BK", "Black"),
            ("BL", "Blue"),
            ("RD", "Red"),
            ("GN", "Green"),
            ("BN", "Brown")
        ],
        validators=[DataRequired()]
    )


    customer_id = SelectField(
        "Customer",
        coerce=int,
        validators=[DataRequired()]
    )

    cable_type_id = SelectField(
        "Cable",
        coerce=int,
        validators=[DataRequired()]
    )

    production_line_id = SelectField(
        "Production Line",
        coerce=int,
        validators=[DataRequired()]
    )

    production_date = DateField(
        "Production Date",
        format="%Y-%m-%d",
        validators=[DataRequired()]
    )

    cable_length = FloatField(
        "Cable Length (m)",
        validators=[DataRequired()]
    )

    status = SelectField(
        "Status",
        choices=[
            ("Pending", "Pending"),
            ("Completed", "Completed"),
            ("Rejected", "Rejected")
        ],
        default ="Pending"
    )

    submit = SubmitField("Save Batch")

class CustomerForm(FlaskForm):

    company_name = StringField(
        "Company Name",
        validators=[DataRequired()]
    )

    contact_person = StringField(
        "Contact Person",
        validators=[Optional()]
    )

    email = StringField(
        "Email",
        validators=[Optional(), Email()]
    )

    phone = StringField(
        "Phone",
        validators=[Optional()]
    )

    address = TextAreaField(
        "Address",
        validators=[Optional()]
    )

    submit = SubmitField("Save Customer")

class CableTypeForm(FlaskForm):

    pair_count = SelectField(
        "Pair",
        choices=[
            ("1P","1P"),
            ("2P","2P"),
            ("5P","5P"),
            ("8P","8P"),
            ("10P","10P"),
            ("20P","20P")
        ],
        validators=[DataRequired()]
    )

    conductor_size = SelectField(
        "Conductor Size",
        choices=[
            ("1.0mm²","1.0mm²"),
            ("1.5mm²","1.5mm²"),
            ("2.5mm²","2.5mm²"),
            ("4.0mm²","4.0mm²")
        ],
        validators=[DataRequired()]
    )

    voltage_rating = SelectField(
        "Voltage Rating",
        choices=[
            ("300/500V","300/500V"),
            ("600/1000V","600/1000V")
        ],
        validators=[DataRequired()]
    )

    drain_configuration = SelectField(
        "Drain Configuration",
        choices=[
            ("OS","OS"),
            ("IS-OS","IS-OS")
        ],
        validators=[DataRequired()]
    )

    conductor_material = SelectField(
        "Conductor",
        choices=[
            ("CU(SOL)","CU(SOL)"),
            ("CU(STRD)","CU(STRD)")
        ],
        validators=[DataRequired()]
    )

    insulation_material = SelectField(
        "Insulation",
        choices=[
            ("XLPE","XLPE"),
            ("PVC","PVC")
        ],
        validators=[DataRequired()]
    )

    fire_resistant_material = SelectField(
        "Fire Resistant Material",
        choices=[
            ("MICA","MICA"),
            ("NONE","NONE")
        ]
    )

    inner_sheath_material = SelectField(
        "Inner Sheath",
        choices=[
            ("LSZH","LSZH"),
            ("PVC","PVC")
        ]
    )

    armour_type = SelectField(
        "Armour",
        choices=[
            ("SWA","SWA"),
            ("FLAT","FLAT")
        ]
    )

    outer_sheath_material = SelectField(
        "Outer Sheath",
        choices=[
            ("LSZH","LSZH"),
            ("PVC","PVC")
        ]
    )

    flame_retardant = SelectField(
        "Flame Retardant",
        choices=[
            ("FR","FR"),
            ("NONE","NONE")
        ]
    )

    application = TextAreaField(
        "Application",
        validators=[Optional()]
    )

    submit = SubmitField("Save Cable Type")

class ProductionLineForm(FlaskForm):

    line_name = StringField(
        "Production Line",
        validators=[DataRequired(), Length(max=100)]
    )

    location = StringField(
        "Location",
        validators=[DataRequired()]
    )

    supervisor = StringField(
        "Supervisor",
        validators=[DataRequired()]
    )

    status = SelectField(
        "Status",
        choices=[
            ("Active", "Active"),
            ("Inactive", "Inactive"),
            ("Maintenance", "Maintenance")
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField("Save Production Line")

class InspectionForm(FlaskForm):

    batch_id = SelectField(
        "Cable Batch",
        coerce=int,
        validators=[DataRequired()]
    )

    inspector = StringField(
        "Inspector",
        validators=[DataRequired()]
    )


    remarks = TextAreaField(
        "Remarks"
    )

    inspection_date = DateField(
        "Inspection Date",
        format="%Y-%m-%d",
        validators=[DataRequired()]
    )

    submit = SubmitField("Save Inspection")


class QualityMetricForm(FlaskForm):

    specification_id = SelectField(
        "Quality Metric (Test)",
        coerce=int,
        validators=[DataRequired()]
    )

    unit = StringField(
        "Unit",
        render_kw={"readonly": True}
    )

    minimum_value = FloatField(
        "Minimum",
        render_kw={"readonly": True}
    )

    maximum_value = FloatField(
        "Maximum",
        render_kw={"readonly": True}
    )

    expected_text = StringField(
        "Expected Result",
        render_kw={"readonly": True}
    )

    measured_value = StringField(
        "Measured Value",
        validators=[DataRequired()]
    )

    submit = SubmitField("Save Quality Metric")
class QualitySpecificationForm(FlaskForm):

    cable_type_id = SelectField(
        "Cable Name",
        coerce=int,
        validators=[DataRequired()]
    )

    metric_name = SelectField(
        "Metric",
        choices=[

            ("Length", "Length"),

            ("Conductor Design", "Conductor Design"),

            ("Conductor Elongation @ break",
             "Conductor Elongation @ break"),

            ("DC Conductor Resistance @ 20°C",
             "DC Conductor Resistance @ 20°C"),

            ("Core Colour",
             "Core Colour"),

            ("Insulation Thickness",
             "Insulation Thickness"),

            ("Spark Test On Insulation",
             "Spark Test On Insulation"),

            ("Inner Sheath Thickness",
             "Inner Sheath Thickness"),

            ("Diameter Over Inner Sheath",
             "Diameter Over Inner Sheath"),

            ("Nominal Armor Diameter",
             "Nominal Armor Diameter"),

            ("Diameter Over Armouring",
             "Diameter Over Armouring"),

            ("Outer Sheath Thickness",
             "Outer Sheath Thickness"),

            ("Diameter Over Sheathing",
             "Diameter Over Sheathing"),

            ("Hot Set Test @ 200°C For 15 Minutes",
             "Hot Set Test @ 200°C For 15 Minutes"),

            ("Insulation Resistance @ 20°C Measured @ 1000 Vdc For 1 Minute",
             "Insulation Resistance @ 20°C Measured @ 1000 Vdc For 1 Minute"),

            ("Water Absorption Test @ 90°C",
             "Water Absorption Test @ 90°C"),

            ("Water Penetration Test For 6m Cable Sample For 24 Hours",
             "Water Penetration Test For 6m Cable Sample For 24 Hours"),

            ("Sheath Elongation",
             "Sheath Elongation"),

            ("Sheath Tensile Strength",
             "Sheath Tensile Strength"),

            ("Flame Retardant Test",
             "Flame Retardant Test"),

            ("Continuity",
             "Continuity"),

            ("HVT Test @ 1.5KV For 5 Minutes",
             "HVT Test @ 1.5KV For 5 Minutes")

        ],
        validators=[DataRequired()]
    )

    unit = StringField(
        "Unit"
    )

    validation_type = SelectField(
        "Validation Type",
        choices=[
            ("any", "Accept Any Value"),
            ("minimum", "Minimum"),
            ("maximum", "Maximum"),
            ("range", "Range (Min & Max)"),
            ("text", "Text Comparison")
        ],
        validators=[DataRequired()]
    )

    minimum_value = FloatField(
        "Minimum Value",
        default=0
    )

    maximum_value = FloatField(
        "Maximum Value",
        default=0
    )

    requirement = StringField(
        "Requirement / Desired Value"
    )

    expected_result = StringField(
        "Expected Result"
    )

    non_conformance_message = TextAreaField(
        "Non-Conformance Message"
    )

    submit = SubmitField(
        "Save Specification"
    )

class DeviationForm(FlaskForm):

    description = TextAreaField(
        "Description",
        validators=[DataRequired()]
    )

    severity = SelectField(
        "Severity",
        choices=[
            ("Minor", "Minor"),
            ("Major", "Major"),
            ("Critical", "Critical")
        ]
    )

    root_cause = TextAreaField("Root Cause")

    status = SelectField(
        "Status",
        choices=[
            ("Open", "Open"),
            ("In Progress", "In Progress"),
            ("Closed", "Closed")
        ]
    )

    reported_by = StringField(
        "Reported By",
        validators=[DataRequired()]
    )

    submit = SubmitField("Save Deviation")


class CAPAForm(FlaskForm):

    corrective_action = TextAreaField(
        "Corrective Action",
        validators=[DataRequired()]
    )

    preventive_action = TextAreaField(
        "Preventive Action",
        validators=[DataRequired()]
    )

    assigned_to = StringField(
        "Assigned To",
        validators=[DataRequired()]
    )

    due_date = DateField(
        "Due Date",
        format="%Y-%m-%d"
    )

    completion_date = DateField(
        "Completion Date",
        format="%Y-%m-%d",
        validators=[Optional()]
    )

    effectiveness = SelectField(
        "Effectiveness",
        choices=[
            ("Pending","Pending"),
            ("Effective","Effective"),
            ("Not Effective","Not Effective")
        ]
    )

    status = SelectField(
        "Status",
        choices=[
            ("Open","Open"),
            ("In Progress","In Progress"),
            ("Completed", "Completed"),
            ("Overdue", "Overdue"),
            ("Closed","Closed")
        ]
    )

    submit = SubmitField("Save CAPA")

#theme form
class ThemeSettingsForm(FlaskForm):

    theme = SelectField(
        "Theme",
        choices=[
            ("light", "Light"),
            ("dark", "Dark"),
            ("system", "System Default")
        ]
    )

    submit = SubmitField("Save Changes")


class AccountSettingsForm(FlaskForm):

    full_name = StringField(
        "Full Name",
        validators=[
            DataRequired(),
            Length(max=120)
        ]
    )

    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(max=50)
        ]
    )

    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Email()
        ]
    )

    submit = SubmitField(
        "Save Changes"
    )


class ChangePasswordForm(FlaskForm):

    current_password = PasswordField(
        "Current Password",
        validators=[
            DataRequired()
        ]
    )

    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters.")
        ]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo(
                "new_password",
                message="Passwords must match."
            )
        ]
    )

    submit = SubmitField("Change Password")

class NotificationSettingsForm(FlaskForm):

    notification_enabled = BooleanField(
        "Enable Notifications"
    )

    inspection_notification = BooleanField(
        "Inspection Notifications"
    )

    deviation_notification = BooleanField(
        "Deviation Notifications"
    )

    capa_notification = BooleanField(
        "CAPA Notifications"
    )

    failure_sound = BooleanField(
        "Play Sound When Inspection Fails"
    )

    submit = SubmitField(
        "Save Preferences"
    )
