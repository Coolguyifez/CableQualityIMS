import os


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:

    SECRET_KEY = os.environ.get(
        "SECRET_KEY"
    )

    DATABASE_URL = os.environ.get("DATABASE_URL")

    if DATABASE_URL:

        if DATABASE_URL.startswith("postgres://"):

            DATABASE_URL = DATABASE_URL.replace(
                "postgres://",
                "postgresql://",
                1
            )

        SQLALCHEMY_DATABASE_URI = DATABASE_URL

    else:

        SQLALCHEMY_DATABASE_URI = (
            "sqlite:///" +
            os.path.join(
                BASE_DIR,
                "instance",
                "cable_quality.db"
            )
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
