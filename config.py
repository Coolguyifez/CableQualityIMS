
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:

    # =========================
    # SECRET KEY
    # =========================

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "change-this-later"
    )

    # =========================
    # DATABASE
    # =========================

    database_url = os.environ.get("DATABASE_URL")

    # Render/older PostgreSQL URLs may use postgres://
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    SQLALCHEMY_DATABASE_URI = (
        database_url
        or "sqlite:///"
        + os.path.join(
            BASE_DIR,
            "instance",
            "cable_quality.db"
        )
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
