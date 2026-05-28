import os
# Tambahkan inspect dan text di baris ini
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FUNGSI DDL / MIGRASI MANUAL ---
def ensure_column(engine, table_name: str, column_name: str, column_type_sql: str):
    inspector = inspect(engine)
    if not inspector.has_table(table_name):
        return # Skip jika tabel belum ada
    columns = [c["name"] for c in inspector.get_columns(table_name)]
    if column_name in columns:
        return
    preparer = engine.dialect.identifier_preparer
    table_quoted = preparer.quote(table_name)
    column_quoted = preparer.quote(column_name)
    ddl = f"ALTER TABLE {table_quoted} ADD COLUMN {column_quoted} {column_type_sql}"
    with engine.begin() as conn:
        conn.execute(text(ddl))

def ensure_nik_columns():
    ensure_column(engine, "keluarga", "nik", "VARCHAR(100)")
    ensure_column(engine, "keluarga_history", "nik", "VARCHAR(100)")

ensure_nik_columns()