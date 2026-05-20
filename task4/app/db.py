from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from config import DATABASE_URL

_engine: Engine = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        if not DATABASE_URL:
            raise RuntimeError("DATABASE_URL is not set in environment")
        _engine = create_engine(DATABASE_URL, future=True)
    return _engine
