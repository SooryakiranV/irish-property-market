import os
from dataclasses import dataclass

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine, URL


@dataclass(frozen=True)
class DatabaseConfig:
    host: str
    port: int
    database: str
    user: str
    password: str


def load_database_config() -> DatabaseConfig:
    """Load PostgreSQL connection settings from environment variables."""

    load_dotenv()

    return DatabaseConfig(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "irish_property_market"),
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", ""),
    )


def create_postgres_engine(config: DatabaseConfig | None = None) -> Engine:
    """Create a SQLAlchemy engine for the project PostgreSQL database."""

    if config is None:
        config = load_database_config()

    url = URL.create(
        drivername="postgresql+psycopg2",
        username=config.user,
        password=config.password,
        host=config.host,
        port=config.port,
        database=config.database,
    )

    return create_engine(url, future=True)

