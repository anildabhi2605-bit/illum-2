"""Persistence layer for ILLUM AI STUDIO (P03-T02).

Exports SQLAlchemy 2.0 models, database connection helpers, OS-level locks,
and migration/recovery runners.
"""

from app.persistence.database import (
    DEFAULT_DB_PATH,
    configure_database_wal,
    create_sqlite_connection,
    get_engine,
    get_session_factory,
    init_database_tables,
    set_connection_pragmas,
)
from app.persistence.lock import DatabaseLockedError, FileLock, database_lock
from app.persistence.migrations import (
    MigrationError,
    MigrationStateAmbiguousError,
    atomic_restore_from_backup,
    create_consistent_backup,
    inspect_migration_state_on_startup,
    quarantine_database_and_sidecars,
    run_migrations_downgrade,
    run_migrations_upgrade,
    verify_database_integrity,
)
from app.persistence.models import (
    ALLOWED_ERROR_CATEGORIES,
    ALLOWED_ERROR_CODES,
    ALLOWED_FALLBACK_REASONS,
    SCHEMA_SQL_DDL,
    AnalysisModel,
    ApprovalModel,
    Base,
    CurrentScriptModel,
    ExecutionEventModel,
    GeneratedOutputModel,
    ProjectModel,
    SourceVersionModel,
)
from app.persistence.exceptions import (
    ConstraintViolationError,
    EntityNotFoundError,
    ProjectMismatchError,
    RepositoryError,
)
from app.persistence.repositories import (
    AnalysisRepository,
    ApprovalRepository,
    BaseRepository,
    CurrentScriptRepository,
    ExecutionEventRepository,
    GeneratedOutputRepository,
    ProjectRepository,
    SourceVersionRepository,
)

__all__ = [
    # Repositories & Exceptions
    "RepositoryError",
    "EntityNotFoundError",
    "ProjectMismatchError",
    "ConstraintViolationError",
    "BaseRepository",
    "ProjectRepository",
    "SourceVersionRepository",
    "AnalysisRepository",
    "CurrentScriptRepository",
    "ApprovalRepository",
    "GeneratedOutputRepository",
    "ExecutionEventRepository",
    # Database initialization & connections
    "DEFAULT_DB_PATH",
    "configure_database_wal",
    "create_sqlite_connection",
    "init_database_tables",
    "set_connection_pragmas",
    "get_engine",
    "get_session_factory",
    # OS file lock
    "DatabaseLockedError",
    "FileLock",
    "database_lock",
    # Migrations, backups, & recovery
    "MigrationError",
    "MigrationStateAmbiguousError",
    "create_consistent_backup",
    "verify_database_integrity",
    "quarantine_database_and_sidecars",
    "atomic_restore_from_backup",
    "inspect_migration_state_on_startup",
    "run_migrations_upgrade",
    "run_migrations_downgrade",
    # Schema, DDL, & models
    "SCHEMA_SQL_DDL",
    "ALLOWED_ERROR_CATEGORIES",
    "ALLOWED_ERROR_CODES",
    "ALLOWED_FALLBACK_REASONS",
    "Base",
    "ProjectModel",
    "SourceVersionModel",
    "AnalysisModel",
    "CurrentScriptModel",
    "ApprovalModel",
    "GeneratedOutputModel",
    "ExecutionEventModel",
]
