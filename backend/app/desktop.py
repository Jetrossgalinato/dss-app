from __future__ import annotations

import argparse
import logging
import os
from pathlib import Path
import sys


def sqlite_url(database_path: Path) -> str:
    return f"sqlite+pysqlite:///{database_path.resolve().as_posix()}"


def resource_root() -> Path:
    bundled_root = getattr(sys, "_MEIPASS", None)
    if bundled_root:
        return Path(bundled_root)
    return Path(__file__).resolve().parents[1]


def run_migrations(database_url: str) -> None:
    from alembic import command
    from alembic.config import Config

    root = resource_root()
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(config, "head")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Enrollment DSS desktop backend")
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--log-file", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.database.parent.mkdir(parents=True, exist_ok=True)
    args.log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=args.log_file,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    database_url = sqlite_url(args.database)
    os.environ["DATABASE_URL"] = database_url
    os.environ["API_TOKEN"] = args.token
    os.environ["DESKTOP_MODE"] = "true"

    try:
        run_migrations(database_url)

        import uvicorn

        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=args.port,
            log_config=None,
            access_log=False,
        )
    except Exception:
        logging.exception("Desktop backend failed.")
        raise


if __name__ == "__main__":
    main()
