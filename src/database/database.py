"""
Database connection and session management for the AI Coding Assistant Evaluation Framework.
"""

import json
import os
from pathlib import Path
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from .models import Base


class DatabaseManager:
    """Manages database connections and operations."""
    
    def __init__(self, config_path: str = "config/database.json"):
        """Initialize database manager with configuration."""
        self.config = self._load_config(config_path)
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def _load_config(self, config_path: str) -> dict:
        """Load database configuration from JSON file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Database config file not found: {config_path}")
            
        with open(config_file, 'r') as f:
            return json.load(f)
    
    def _create_engine(self) -> Engine:
        """Create SQLAlchemy engine with proper configuration."""
        db_config = self.config['database']
        
        # Ensure database directory exists
        db_path = Path(db_config['path'])
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create SQLite engine
        engine = create_engine(
            f"sqlite:///{db_path}",
            poolclass=StaticPool,
            pool_pre_ping=True,
            connect_args={
                "check_same_thread": False,
                "timeout": db_config.get('query_timeout_ms', 30000) / 1000
            }
        )
        
        # Enable WAL mode and foreign keys if configured
        if db_config.get('enable_wal_mode', True):
            @event.listens_for(engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")
                if db_config.get('enable_foreign_keys', True):
                    cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
        
        return engine
    
    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def drop_tables(self):
        """Drop all database tables (use with caution)."""
        Base.metadata.drop_all(bind=self.engine)
    
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with proper cleanup."""
        session = self.SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    def backup_database(self, backup_path: str = None) -> str:
        """Create a backup of the database."""
        if backup_path is None:
            backup_dir = Path(self.config['database'].get('backup_path', './data/backups/'))
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"evaluation_framework_backup_{timestamp}.db"
        
        # Simple file copy for SQLite
        import shutil
        db_path = Path(self.config['database']['path'])
        shutil.copy2(db_path, backup_path)
        
        return str(backup_path)
    
    def get_database_info(self) -> dict:
        """Get information about the database."""
        with next(self.get_session()) as session:
            # Get table count and row counts
            tables_info = {}
            for table_name in Base.metadata.tables.keys():
                count_query = f"SELECT COUNT(*) FROM {table_name}"
                result = session.execute(count_query).scalar()
                tables_info[table_name] = result
            
        return {
            "database_path": self.config['database']['path'],
            "tables": tables_info,
            "total_tables": len(tables_info)
        }


# Global database manager instance
db_manager = DatabaseManager()


def get_db() -> Generator[Session, None, None]:
    """Dependency function for FastAPI to get database sessions."""
    yield from db_manager.get_session()


def init_database():
    """Initialize the database with tables."""
    db_manager.create_tables()
    
    # Create initial views
    with next(db_manager.get_session()) as session:
        # Session summary view
        session.execute("""
            CREATE VIEW IF NOT EXISTS session_summary AS
            SELECT 
                ts.id,
                ts.session_name,
                ts.tool_name,
                ts.test_case_type,
                ts.start_time,
                ts.end_time,
                ROUND((julianday(ts.end_time) - julianday(ts.start_time)) * 24 * 60, 2) as duration_minutes,
                COUNT(DISTINCT ai.id) as ai_interactions_count,
                COUNT(DISTINCT cc.id) as code_changes_count,
                AVG(df.overall_satisfaction) as avg_satisfaction,
                ts.status
            FROM test_sessions ts
            LEFT JOIN ai_interactions ai ON ts.id = ai.session_id
            LEFT JOIN code_changes cc ON ts.id = cc.session_id
            LEFT JOIN developer_feedback df ON ts.id = df.session_id
            GROUP BY ts.id, ts.session_name, ts.tool_name, ts.test_case_type, ts.start_time, ts.end_time, ts.status
        """)
        
        # Tool comparison view
        session.execute("""
            CREATE VIEW IF NOT EXISTS tool_comparison AS
            SELECT 
                tool_name,
                test_case_type,
                COUNT(*) as sessions_count,
                AVG(duration_minutes) as avg_duration_minutes,
                AVG(ai_interactions_count) as avg_ai_interactions,
                AVG(code_changes_count) as avg_code_changes,
                AVG(avg_satisfaction) as avg_satisfaction_rating
            FROM session_summary 
            WHERE status = 'completed'
            GROUP BY tool_name, test_case_type
        """)
        
        session.commit()


if __name__ == "__main__":
    # Initialize database when run directly
    print("Initializing database...")
    init_database()
    print("Database initialized successfully!")
    
    # Print database info
    info = db_manager.get_database_info()
    print(f"Database created at: {info['database_path']}")
    print(f"Total tables: {info['total_tables']}")
    for table, count in info['tables'].items():
        print(f"  {table}: {count} rows")