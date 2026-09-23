import os
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

# Global engine and Session factory
engine = None
Session = None

def init_hr_db(db_config):
    global engine, Session
    if db_config:
        db_url = URL.create(
            "mysql+mysqlconnector",
            username=db_config['user'],
            password=db_config['password'],
            host=db_config['host'],
            port=db_config.get('port', 3306),
            database=db_config['database'],
        )
    else:
        raise ValueError("Database configuration (db_config) must be provided to init_hr_db.")

    engine = create_engine(db_url, echo=False, future=True, poolclass=QueuePool, pool_size=10, max_overflow=20)
    Session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
    
    from hr_models import Base
    Base.metadata.create_all(engine)

def get_session():
    if Session is None:
        raise RuntimeError("HR database not initialized. Call init_hr_db() first.")
    return Session()
