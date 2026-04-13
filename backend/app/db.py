from sqlmodel import create_engine, SQLModel, Session
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL, echo=settings.DEBUG if hasattr(settings, "DEBUG") else False
)


def init_db():
    import os

    if os.environ.get("TESTING") == "1":
        SQLModel.metadata.create_all(engine)
    elif os.environ.get("_MIGRATIONS_DONE") != "1":
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        os.environ["_MIGRATIONS_DONE"] = "1"


def get_session():
    with Session(engine) as session:
        yield session
