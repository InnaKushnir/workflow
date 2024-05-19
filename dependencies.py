from fastapi import Depends
from sqlalchemy.orm import Session
from db.engine import SessionLocal


class DBSession:
    def __init__(self):
        self._session = None

    def __enter__(self):
        self._session = SessionLocal()
        return self._session

    def __exit__(self, exc_type, exc_value, traceback):
        self._session.close()


def get_db() -> Session:
    with DBSession() as db:
        yield db