import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool

# Global engine and Session factory
engine = None
Session = None


def ensure_hr_schema(engine_obj):
    if engine_obj is None:
        return

    try:
        from hr_models import Base
        Base.metadata.create_all(engine_obj)
    except Exception:
        return

    dialect_name = engine_obj.dialect.name
    if dialect_name != 'mysql':
        return

    try:
        inspector = inspect(engine_obj)
        if 'employees' not in inspector.get_table_names():
            return

        columns = {column['name'] for column in inspector.get_columns('employees')}
        with engine_obj.begin() as conn:
            additions = {
                'department_id': 'ALTER TABLE employees ADD COLUMN department_id INT NULL',
                'job_title': 'ALTER TABLE employees ADD COLUMN job_title VARCHAR(128) NULL',
                'phone': 'ALTER TABLE employees ADD COLUMN phone VARCHAR(32) NULL',
                'email': 'ALTER TABLE employees ADD COLUMN email VARCHAR(128) NULL',
                'status': 'ALTER TABLE employees ADD COLUMN status VARCHAR(30) DEFAULT "Active"',
            }
            for column_name, statement in additions.items():
                if column_name not in columns:
                    conn.execute(text(statement))
    except Exception:
        pass


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

    ensure_hr_schema(engine)


def get_session():
    if Session is None:
        raise RuntimeError("HR database not initialized. Call init_hr_db() first.")
    return Session()
