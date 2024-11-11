import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from typing import Any, Optional
from contextlib import contextmanager
from typing_extensions import Self

from sqlalchemy.sql.type_api import _T
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, dialects, engine, pool, types
from sqlalchemy.orm import sessionmaker, scoped_session, Session as SQLAlchemySession


class JSONField(types.TypeDecorator):
    impl = types.Text
    cache_ok = True

    def process_bind_param(self, value: Optional[_T], dialect: dialects) -> Any:
        return json.dumps(value)

    def process_result_value(self, value: Optional[_T], dialect: dialects) -> Any:
        if value is not None:
            return json.loads(value)

    def copy(self, **kw: Any) -> Self:
        return JSONField(self.impl.length)
        
    def db_value(self, value):
        return json.dumps(value)

    def python_value(self, value):
        if value is not None:
            return json.loads(value)


current_dir = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(current_dir, '../../../../data/vica.db')
DATABASE_URL = f"sqlite:////{DB_PATH}"

if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)
Base = declarative_base()
Session = scoped_session(SessionLocal)

def get_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

get_db = contextmanager(get_session)