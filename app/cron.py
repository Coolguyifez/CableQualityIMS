from datetime import date

from app import create_app
from app.extensions import db
from app.models import CAPA


def process_overdue_capas():

    app = create_app()

    with app.app_context():

        print("\n================================")
        print("CAPA CRON STARTED")
        print("Today's date:", date.today())
        print("================================\n")

        capas = CAPA.query.all()

        print("Total CAPAs found:", len(capas))

        for capa in capas:

            print("\n-------------------------------")
            print("CAPA ID:", capa.id)
            print("CAPA Status:", capa.status)
            print("Due Date:", capa.due_date)

            if capa.status in ["Completed", "Closed"]:
                print("SKIPPED: Completed/Closed")
                continue

            if not capa.due_date:
                print("SKIPPED: No due date")
                continue

            if date.today() > capa.due_date:

                print("RESULT: CAPA IS OVERDUE")

                # Change CAPA status
                if capa.status != "Overdue":

                    capa.status = "Overdue"

                    print("CAPA status changed to Overdue")

                else:

                    print("CAPA was already Overdue")

                # -----------------------------------------
                # Find Production Line
                # -----------------------------------------

                try:

                    deviation = capa.deviation

                    print(
                        "Deviation:",
                        deviation.deviation_number
                        if deviation else "NONE"
                    )

                    inspection = deviation.inspection

                    print(
                        "Inspection:",
                        inspection.id
                        if inspection else "NONE"
                    )

                    batch = inspection.batch

                    print(
                        "Batch:",
                        batch.batch_number
                        if batch else "NONE"
                    )

                    production_line = batch.production_line

                    print(
                        "Production Line:",
                        production_line.line_name
                        if production_line else "NONE"
                    )

                    print(
                        "Production Line Status:",
                        production_line.status
                        if production_line else "NONE"
                    )

                    if production_line:

                        if production_line.status == "Active":

                            production_line.status = "Maintenance"

                            print(
                                "SUCCESS: Production line "
                                "changed to Maintenance"
                            )

                        else:

                            print(
                                "Production line was NOT Active."
                            )

                except Exception as e:

                    print(
                        "ERROR FINDING PRODUCTION LINE:"
                    )

                    print(type(e).__name__)
                    print(str(e))

            else:

                print("RESULT: CAPA IS NOT OVERDUE")

        db.session.commit()

        print("\n================================")
        print("CAPA CRON FINISHED")
        print("================================\n")


if __name__ == "__main__":
    process_overdue_capas()

