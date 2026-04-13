import os
import sys
import traceback


def main():
    port = int(os.environ.get("PORT", "8000"))
    print(f"[startup] Starting OpenSNS backend on port {port}", flush=True)

    # Step 1: Validate settings load
    print("[startup] Step 1: Loading settings...", flush=True)
    try:
        from app.core.config import settings  # noqa: F401

        print("[startup] Settings loaded OK", flush=True)
    except Exception:
        print("[startup] FATAL: Settings validation failed:", flush=True)
        traceback.print_exc()
        sys.exit(1)

    # Step 2: Test DB connection
    print("[startup] Step 2: Testing database connection...", flush=True)
    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1")).fetchone()
        print("[startup] Database connection OK", flush=True)
        engine.dispose()
    except Exception:
        print("[startup] FATAL: Database connection failed:", flush=True)
        traceback.print_exc()
        sys.exit(1)

    # Step 3: Run alembic migrations
    print("[startup] Step 3: Running migrations...", flush=True)
    try:
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config("alembic.ini")
        command.upgrade(alembic_cfg, "head")
        os.environ["_MIGRATIONS_DONE"] = "1"
        print("[startup] Migrations completed OK", flush=True)
    except Exception:
        print("[startup] FATAL: Migration failed:", flush=True)
        traceback.print_exc()
        sys.exit(1)

    # Step 4: Start uvicorn (lifespan handles engine registration)
    print(f"[startup] Step 4: Starting uvicorn on 0.0.0.0:{port}...", flush=True)
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
