"""WAL-safe backup, crash-safe coordinated quarantine, and migration safety for ILLUM AI STUDIO (P03-T02).

Governed by:
- ADR-001 Section 3.3: Migration rollback and backup safety
- SQLite Online Backup API for transactionally consistent snapshots in WAL mode
- Coordinated multi-file quarantine handling main DB and active sidecars (-wal, -shm)
- Startup fail-closed ambiguity gate prohibiting automatic destructive cleanup
- DEC-018: Shared .env absolute preservation
"""

from __future__ import annotations

import datetime
import shutil
import sqlite3
import time
from pathlib import Path
from typing import Optional

from app.persistence.database import DEFAULT_DB_PATH, configure_database_wal, init_database_tables
from app.persistence.lock import database_lock


class MigrationError(RuntimeError):
    """Base exception for database migration errors."""
    pass


class MigrationStateAmbiguousError(MigrationError):
    """Raised when migration state is interrupted or ambiguous, halting startup without destructive auto-cleanup."""
    pass


def verify_database_integrity(db_path: Path) -> bool:
    """Run PRAGMA quick_check on SQLite database file to verify integrity."""
    if not db_path.exists():
        return False
    try:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA quick_check;")
            row = cursor.fetchone()
            if row and str(row[0]).lower() == "ok":
                return True
            return False
    except (sqlite3.DatabaseError, OSError):
        return False


def create_consistent_backup(source_db_path: Path, backup_db_path: Path) -> Path:
    """Create a transactionally consistent backup using SQLite Online Backup API.

    Safely captures live uncheckpointed WAL frames from source_db_path-wal.
    Verifies backup integrity before returning.
    """
    if not source_db_path.exists():
        raise FileNotFoundError(f"Source database file does not exist: {source_db_path}")

    backup_db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(str(source_db_path)) as src_conn:
        with sqlite3.connect(str(backup_db_path)) as dst_conn:
            src_conn.backup(dst_conn, pages=100)

    # Immediately verify backup integrity
    if not verify_database_integrity(backup_db_path):
        if backup_db_path.exists():
            backup_db_path.unlink()
        raise MigrationError(f"Backup verification failed: {backup_db_path} is corrupted.")

    return backup_db_path


def quarantine_database_and_sidecars(
    db_path: Path,
    quarantines_dir: Optional[Path] = None,
) -> Path:
    """Coordinated multi-file quarantine of main database and active sidecars (-wal, -shm).

    Uses a staging directory with an .in_progress marker, sequentially moves files,
    and atomically renames the directory upon completion to prevent corrupted sidecar replay.
    """
    target_quarantines = quarantines_dir if quarantines_dir is not None else db_path.parent / "quarantines"
    target_quarantines.mkdir(parents=True, exist_ok=True)

    timestamp = int(time.time() * 1000)
    staging_dir = target_quarantines / f"quarantine_{timestamp}.in_progress"
    staging_dir.mkdir(parents=True, exist_ok=False)

    sidecar_wal = Path(str(db_path) + "-wal")
    sidecar_shm = Path(str(db_path) + "-shm")

    # Sequentially move main and sidecars into staging directory
    if db_path.exists():
        shutil.move(str(db_path), str(staging_dir / db_path.name))
    if sidecar_wal.exists():
        shutil.move(str(sidecar_wal), str(staging_dir / sidecar_wal.name))
    if sidecar_shm.exists():
        shutil.move(str(sidecar_shm), str(staging_dir / sidecar_shm.name))

    # Atomically rename directory to remove .in_progress marker
    final_dir = target_quarantines / f"quarantine_{timestamp}"
    staging_dir.rename(final_dir)
    return final_dir


def atomic_restore_from_backup(backup_db_path: Path, target_db_path: Path) -> None:
    """Atomically restore verified pre-migration backup to target database path via temporary sibling file."""
    if not backup_db_path.exists():
        raise FileNotFoundError(f"Verified backup not found: {backup_db_path}")

    # Verify backup before restoring
    if not verify_database_integrity(backup_db_path):
        raise MigrationError(f"Pre-migration backup failed integrity check: {backup_db_path}")

    target_db_path.parent.mkdir(parents=True, exist_ok=True)
    temp_restore = target_db_path.parent / (target_db_path.name + ".restore_tmp")

    # Copy backup to temporary sibling
    shutil.copy2(str(backup_db_path), str(temp_restore))

    # Verify temporary file
    if not verify_database_integrity(temp_restore):
        if temp_restore.exists():
            temp_restore.unlink()
        raise MigrationError(f"Temporary restored database failed integrity check: {temp_restore}")

    # Atomically rename temporary file over target
    temp_restore.replace(target_db_path)

    # Post-restore verification
    if not verify_database_integrity(target_db_path):
        raise MigrationError(f"Restored database failed final integrity check: {target_db_path}")

    # Re-verify WAL mode
    configure_database_wal(target_db_path)


def inspect_migration_state_on_startup(
    db_path: Path = DEFAULT_DB_PATH,
    quarantines_dir: Optional[Path] = None,
) -> None:
    """Startup-time fail-closed inspection.

    If an in-flight migration marker or partial quarantine directory is detected:
    STRICTLY PROHIBITS automatic cleanup, deletion, or destructive auto-restore.
    Halts application startup with MigrationStateAmbiguousError.
    """
    target_quarantines = quarantines_dir if quarantines_dir is not None else db_path.parent / "quarantines"

    # 1. Check for interrupted partial quarantine directories
    if target_quarantines.exists():
        in_progress_dirs = [
            d for d in target_quarantines.iterdir()
            if d.is_dir() and d.name.endswith(".in_progress")
        ]
        if in_progress_dirs:
            raise MigrationStateAmbiguousError(
                f"STARTUP HALTED: Interrupted database quarantine detected at {in_progress_dirs[0]}. "
                "Automatic cleanup, deletion, or restore is strictly prohibited to prevent data loss. "
                "Inspect the staging quarantine directory and manual backups before restarting."
            )

    # 2. Check for in-flight migration marker
    marker_path = db_path.parent / (db_path.name + ".migration_in_progress")
    if marker_path.exists():
        raise MigrationStateAmbiguousError(
            f"STARTUP HALTED: Migration in progress marker detected at {marker_path}. "
            "A previous migration process was abruptly terminated (crash/power failure). "
            "Automatic destructive restore is prohibited. Inspect database state manually."
        )

    # 3. Check database file integrity if present
    if db_path.exists():
        if not verify_database_integrity(db_path):
            raise MigrationStateAmbiguousError(
                f"STARTUP HALTED: Active database {db_path} failed integrity quick_check. "
                "The database file appears corrupted. Automatic restore is prohibited. "
                "Consult verified backups in data/ before manual recovery."
            )


def run_migrations_upgrade(db_path: Path = DEFAULT_DB_PATH) -> None:
    """Execute migration upgrade under exclusive process lock with pre-migration backup and recovery."""
    lock_file = db_path.parent / "illum.lock"
    marker_path = db_path.parent / (db_path.name + ".migration_in_progress")
    backup_file = db_path.parent / "illum.db.bak"

    with database_lock(lock_file):
        has_existing_db = db_path.exists()
        if has_existing_db:
            # Verify and create pre-migration backup
            if verify_database_integrity(db_path):
                create_consistent_backup(db_path, backup_file)
            else:
                raise MigrationError(f"Cannot migrate corrupted database: {db_path}")

        # Set in-flight marker
        marker_path.parent.mkdir(parents=True, exist_ok=True)
        with open(marker_path, "w", encoding="utf-8") as f_mark:
            f_mark.write(f"migration_started_at={datetime.datetime.now(datetime.timezone.utc).isoformat()}\n")

        try:
            # Apply schema tables and indexes
            init_database_tables(db_path)
            # Remove in-flight marker on success
            if marker_path.exists():
                marker_path.unlink()
        except Exception as exc:
            # Caught exception: execute coordinated quarantine and atomic restore
            if marker_path.exists():
                marker_path.unlink()

            if has_existing_db and backup_file.exists():
                quarantine_database_and_sidecars(db_path)
                atomic_restore_from_backup(backup_file, db_path)

            raise MigrationError(f"Migration upgrade failed and was safely rolled back: {exc}") from exc


def run_migrations_downgrade(db_path: Path = DEFAULT_DB_PATH, target_revision: str = "base") -> None:
    """Execute intentional migration downgrade via DDL without restoring from backup."""
    lock_file = db_path.parent / "illum.lock"

    with database_lock(lock_file):
        if not db_path.exists():
            return

        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.cursor()
            # In base downgrade, drop all tables cleanly
            if target_revision == "base":
                cursor.execute("PRAGMA foreign_keys = OFF;")
                tables = [
                    "execution_events",
                    "generated_outputs",
                    "approvals",
                    "current_scripts",
                    "analyses",
                    "source_versions",
                    "projects",
                ]
                for tbl in tables:
                    cursor.execute(f"DROP TABLE IF EXISTS {tbl};")
                cursor.execute("PRAGMA foreign_keys = ON;")
                conn.commit()
