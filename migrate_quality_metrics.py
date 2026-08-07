from sqlalchemy import text
from app import create_app
from app.extensions import db
from app.models import Inspection, QualitySpecification

app = create_app()

with app.app_context():

    print("===== QUALITY METRICS MIGRATION =====")

    # Rename old table
    db.session.execute(
        text("ALTER TABLE quality_metrics RENAME TO quality_metrics_old")
    )

    # Create new table
    db.session.execute(text("""
    CREATE TABLE quality_metrics (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        inspection_id INTEGER NOT NULL,

        specification_id INTEGER NOT NULL,

        measured_value VARCHAR(100) NOT NULL,

        result VARCHAR(20),

        FOREIGN KEY (inspection_id)
            REFERENCES inspections(id),

        FOREIGN KEY (specification_id)
            REFERENCES quality_specifications(id)

    )
    """))

    db.session.commit()

    print("New table created.")

    old_metrics = db.session.execute(text("""
        SELECT
            id,
            inspection_id,
            metric_name,
            measured_value,
            result
        FROM quality_metrics_old
    """)).fetchall()

    migrated = 0

    skipped = 0

    for row in old_metrics:

        inspection = Inspection.query.get(row.inspection_id)

        if inspection is None:
            skipped += 1
            continue

        cable_type_id = inspection.batch.cable_type_id

        specification = QualitySpecification.query.filter_by(
            cable_type_id=cable_type_id,
            metric_name=row.metric_name
        ).first()

        if specification is None:

            print(
                f"Skipped: {row.metric_name} "
                f"(Cable Type {cable_type_id})"
            )

            skipped += 1
            continue

        db.session.execute(text("""
            INSERT INTO quality_metrics
            (
                inspection_id,
                specification_id,
                measured_value,
                result
            )
            VALUES
            (
                :inspection_id,
                :specification_id,
                :measured_value,
                :result
            )
        """), {

            "inspection_id": row.inspection_id,

            "specification_id": specification.id,

            "measured_value": row.measured_value,

            "result": row.result

        })

        migrated += 1

    db.session.commit()

    db.session.execute(
        text("DROP TABLE quality_metrics_old")
    )

    db.session.commit()

    print()

    print("==============================")

    print(f"Migrated : {migrated}")

    print(f"Skipped  : {skipped}")

    print("Migration Complete")

    print("==============================")