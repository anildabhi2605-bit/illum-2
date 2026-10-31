"""Unit tests for ILLUM AI STUDIO database schema, WAL lifecycle, OS locking, and migrations (P03-T02).

Governed by:
- 01_BASELINE/PRODUCT_RULES_AND_INVARIANTS.md
- 02_ARCHITECTURE/DATA_MODEL_AND_RELATIONSHIPS.md
- ADR-001: SQLite local database with SQLAlchemy 2.0 models and Alembic migrations
- ACC-004: Unique project ID and schema persistence
- ACC-007: Referential integrity and tenant isolation
- ACC-018: Single active script table with UNIQUE constraint
- ACC-030B: Metadata-only execution_events schema with triple CHECK constraints
- ACC-032: Foreign key cascade deletion with shared .env preservation
- DEC-018: Strict error and fallback reason allowlist enforcement
"""

import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from uuid import uuid4

from app.domain.constants import PROHIBITED_EXECUTION_EVENT_FIELDS
from app.persistence.database import (
    init_database_tables,
    set_connection_pragmas,
)
from app.persistence.lock import database_lock
from app.persistence.migrations import (
    MigrationStateAmbiguousError,
    create_consistent_backup,
    inspect_migration_state_on_startup,
    quarantine_database_and_sidecars,
    run_migrations_downgrade,
    run_migrations_upgrade,
    verify_database_integrity,
)


class TestDatabaseSchemaAndMigrations(unittest.TestCase):
    """Test suite verifying database creation, constraints, locking, and migrations."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.mkdtemp(prefix="illum_db_test_")
        self.db_path = Path(self.temp_dir) / "test_illum.db"
        self.lock_path = Path(self.temp_dir) / "test_illum.lock"

    def tearDown(self) -> None:
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_clean_database_creation(self):
        """ACC-004: Clean initialization creates all 7 tables and indexes."""
        init_database_tables(self.db_path)
        self.assertTrue(self.db_path.exists())

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cursor.fetchall()}

        expected_tables = {
            "projects",
            "source_versions",
            "analyses",
            "current_scripts",
            "approvals",
            "generated_outputs",
            "execution_events",
        }
        for tbl in expected_tables:
            self.assertIn(tbl, tables, f"Expected table '{tbl}' not found in database")

    def test_sqlite_pragmas_and_wal(self):
        """Assert foreign_keys=ON, journal_mode=WAL, busy_timeout=5000, synchronous=NORMAL."""
        init_database_tables(self.db_path)

        with sqlite3.connect(str(self.db_path)) as conn:
            set_connection_pragmas(conn)
            cursor = conn.cursor()

            cursor.execute("PRAGMA foreign_keys;")
            self.assertEqual(cursor.fetchone()[0], 1)

            cursor.execute("PRAGMA journal_mode;")
            self.assertEqual(str(cursor.fetchone()[0]).lower(), "wal")

            cursor.execute("PRAGMA busy_timeout;")
            self.assertEqual(cursor.fetchone()[0], 5000)

            cursor.execute("PRAGMA synchronous;")
            # synchronous NORMAL corresponds to 1 in SQLite
            self.assertEqual(cursor.fetchone()[0], 1)

    def test_subprocess_file_lock(self):
        """Verify cross-process OS file locking blocks a secondary subprocess."""
        with database_lock(self.lock_path):
            # Attempt to acquire lock from a distinct OS subprocess
            test_script = (
                "import sys\n"
                "from pathlib import Path\n"
                "from app.persistence.lock import FileLock, DatabaseLockedError\n"
                "lock = FileLock(Path(sys.argv[1]))\n"
                "try:\n"
                "    lock.acquire()\n"
                "    sys.exit(0)\n"
                "except DatabaseLockedError:\n"
                "    sys.exit(42)\n"
            )
            result = subprocess.run(
                [sys.executable, "-c", test_script, str(self.lock_path)],
                capture_output=True,
                text=True,
            )
            # Exit code 42 confirms DatabaseLockedError was raised in secondary process
            self.assertEqual(result.returncode, 42, f"Expected returncode 42, got {result.returncode}. Stderr: {result.stderr}")

        # After primary release, secondary acquisition succeeds
        success_script = (
            "import sys\n"
            "from pathlib import Path\n"
            "from app.persistence.lock import FileLock\n"
            "lock = FileLock(Path(sys.argv[1]))\n"
            "lock.acquire()\n"
            "lock.release()\n"
            "sys.exit(0)\n"
        )
        result2 = subprocess.run(
            [sys.executable, "-c", success_script, str(self.lock_path)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result2.returncode, 0, f"Expected returncode 0, got {result2.returncode}. Stderr: {result2.stderr}")

    def test_unique_current_script_constraint(self):
        """ACC-018: current_scripts table strictly enforces UNIQUE(project_id)."""
        init_database_tables(self.db_path)
        pid = str(uuid4())

        with sqlite3.connect(str(self.db_path)) as conn:
            set_connection_pragmas(conn)
            cursor = conn.cursor()
            # Insert project
            cursor.execute(
                "INSERT INTO projects (project_id, title, aspect_ratio, target_width, target_height, "
                "duration_seconds, part_count, content_language, thumbnail_text_language, status, created_at, updated_at) "
                "VALUES (?, 'Test Project', '9:16', 1080, 1920, 24.0, 3, 'en', 'en', 'active', datetime('now'), datetime('now'));",
                (pid,),
            )
            # Insert first current_script
            cursor.execute(
                "INSERT INTO current_scripts (script_id, project_id, title, parts_json, content_hash, source_version_used, "
                "settings_hash, validation_report_json, created_at, updated_at) "
                "VALUES (?, ?, 'Script 1', '[]', 'hash1', 1, 'set1', '{}', datetime('now'), datetime('now'));",
                (str(uuid4()), pid),
            )
            conn.commit()

            # Attempt to insert a SECOND script for the same project_id
            with self.assertRaises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO current_scripts (script_id, project_id, title, parts_json, content_hash, source_version_used, "
                    "settings_hash, validation_report_json, created_at, updated_at) "
                    "VALUES (?, ?, 'Script 2', '[]', 'hash2', 1, 'set2', '{}', datetime('now'), datetime('now'));",
                    (str(uuid4()), pid),
                )

    def test_foreign_key_cascade_deletion(self):
        """ACC-032: Deleting a project cascades to delete all linked child records."""
        init_database_tables(self.db_path)
        pid = str(uuid4())

        with sqlite3.connect(str(self.db_path)) as conn:
            set_connection_pragmas(conn)
            cursor = conn.cursor()

            # Insert project
            cursor.execute(
                "INSERT INTO projects (project_id, title, aspect_ratio, target_width, target_height, "
                "duration_seconds, part_count, content_language, thumbnail_text_language, status, created_at, updated_at) "
                "VALUES (?, 'Cascade Project', '9:16', 1080, 1920, 24.0, 3, 'en', 'en', 'active', datetime('now'), datetime('now'));",
                (pid,),
            )
            # Insert child records in all 6 child tables
            cursor.execute(
                "INSERT INTO source_versions (source_id, project_id, source_version, title, source_type, saved_content, "
                "content_hash, status, created_at, updated_at) VALUES (?, ?, 1, 'Source', 'pasted', 'text', 'h1', 'valid', datetime('now'), datetime('now'));",
                (str(uuid4()), pid),
            )
            cursor.execute(
                "INSERT INTO analyses (analysis_id, project_id, analysis_type, input_hash, output_payload, status, created_at) "
                "VALUES (?, ?, 'source', 'h1', '{}', 'valid', datetime('now'));",
                (str(uuid4()), pid),
            )
            cursor.execute(
                "INSERT INTO current_scripts (script_id, project_id, title, parts_json, content_hash, source_version_used, "
                "settings_hash, validation_report_json, created_at, updated_at) VALUES (?, ?, 'Script', '[]', 'h2', 1, 's1', '{}', datetime('now'), datetime('now'));",
                (str(uuid4()), pid),
            )
            cursor.execute(
                "INSERT INTO approvals (approval_id, project_id, script_hash, settings_hash, status, is_approved, approved_at) "
                "VALUES (?, ?, 'h2', 's1', 'approved', 1, datetime('now'));",
                (str(uuid4()), pid),
            )
            cursor.execute(
                "INSERT INTO generated_outputs (output_id, project_id, kind, input_script_hash, settings_hash, content_json, validation_report_json, status, created_at) "
                "VALUES (?, ?, 'video_prompt', 'h2', 's1', '{}', '{}', 'fresh', datetime('now'));",
                (str(uuid4()), pid),
            )
            cursor.execute(
                "INSERT INTO execution_events (event_id, project_id, job_id, skill_id, status, provider_id, model_id, attempt_count, created_at) "
                "VALUES (?, ?, ?, 'skill_a', 'completed', 'gemini', 'gemini-1.5-flash', 1, datetime('now'));",
                (str(uuid4()), pid, str(uuid4())),
            )
            conn.commit()

            # Delete the parent project row
            cursor.execute("DELETE FROM projects WHERE project_id = ?;", (pid,))
            conn.commit()

            # Verify all 6 child tables cascaded to 0 rows
            child_tables = [
                "source_versions",
                "analyses",
                "current_scripts",
                "approvals",
                "generated_outputs",
                "execution_events",
            ]
            for child in child_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {child} WHERE project_id = ?;", (pid,))
                count = cursor.fetchone()[0]
                self.assertEqual(count, 0, f"Child table '{child}' failed to cascade delete rows for project {pid}")

    def test_shared_env_preservation(self):
        """DEC-018: Database operations strictly preserve shared .env untouched."""
        canary_env = Path(self.temp_dir) / ".env"
        canary_env.write_text("GEMINI_API_KEY=test_canary_secret_12345\n", encoding="utf-8")
        orig_content = canary_env.read_text(encoding="utf-8")

        # Run database initialization, table creation, and teardown
        init_database_tables(self.db_path)
        run_migrations_upgrade(self.db_path)
        run_migrations_downgrade(self.db_path, target_revision="base")

        # Assert .env content is 100% identical and never touched
        self.assertTrue(canary_env.exists())
        self.assertEqual(canary_env.read_text(encoding="utf-8"), orig_content)

    def test_metadata_only_schema_and_check_constraints(self):
        """ACC-030B & DEC-018: execution_events contains metadata only with triple CHECK constraints."""
        init_database_tables(self.db_path)

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(execution_events);")
            columns = {row[1] for row in cursor.fetchall()}

            # Negative invariant: assert zero prohibited fields in table columns
            prohibited_overlap = PROHIBITED_EXECUTION_EVENT_FIELDS.intersection(columns)
            self.assertEqual(
                len(prohibited_overlap),
                0,
                f"Prohibited fields found in execution_events schema: {prohibited_overlap}",
            )

            # Insert project for testing foreign key
            pid = str(uuid4())
            cursor.execute(
                "INSERT INTO projects (project_id, title, aspect_ratio, target_width, target_height, "
                "duration_seconds, part_count, content_language, thumbnail_text_language, status, created_at, updated_at) "
                "VALUES (?, 'P1', '9:16', 1080, 1920, 24.0, 3, 'en', 'en', 'active', datetime('now'), datetime('now'));",
                (pid,),
            )
            conn.commit()

            # Test 1: Valid allowlisted error and fallback codes succeed
            cursor.execute(
                "INSERT INTO execution_events (event_id, project_id, job_id, skill_id, status, provider_id, model_id, "
                "attempt_count, created_at, error_category, error_code, fallback_reason) "
                "VALUES (?, ?, ?, 'skill_a', 'completed', 'gemini', 'gemini-1.5-flash', 1, datetime('now'), "
                "'RATE_LIMIT', 'HTTP_429', 'PRIMARY_PROVIDER_RATE_LIMITED');",
                (str(uuid4()), pid, str(uuid4())),
            )
            conn.commit()

            # Test 2: Unapproved error_category rejected by chk_error_category
            with self.assertRaises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO execution_events (event_id, project_id, job_id, skill_id, status, provider_id, model_id, "
                    "attempt_count, created_at, error_category) "
                    "VALUES (?, ?, ?, 'skill_a', 'failed', 'gemini', 'm1', 1, datetime('now'), 'CUSTOM_UNAPPROVED_CATEGORY');",
                    (str(uuid4()), pid, str(uuid4())),
                )

            # Test 3: Unapproved error_code rejected by chk_error_code
            with self.assertRaises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO execution_events (event_id, project_id, job_id, skill_id, status, provider_id, model_id, "
                    "attempt_count, created_at, error_code) "
                    "VALUES (?, ?, ?, 'skill_a', 'failed', 'gemini', 'm1', 1, datetime('now'), 'UNAPPROVED_ERROR_CODE');",
                    (str(uuid4()), pid, str(uuid4())),
                )

            # Test 4: Freeform/arbitrary fallback_reason rejected by chk_fallback_reason
            with self.assertRaises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO execution_events (event_id, project_id, job_id, skill_id, status, provider_id, model_id, "
                    "attempt_count, created_at, fallback_reason) "
                    "VALUES (?, ?, ?, 'skill_a', 'failed', 'gemini', 'm1', 1, datetime('now'), "
                    "'Raw OpenAI response: Model rate limit exceeded, retry after 20s');",
                    (str(uuid4()), pid, str(uuid4())),
                )

    def test_wal_safe_online_backup(self):
        """Verify transactionally consistent SQLite Online Backup API in WAL mode."""
        init_database_tables(self.db_path)
        pid = str(uuid4())

        # Write data to generate WAL frames
        with sqlite3.connect(str(self.db_path)) as conn:
            set_connection_pragmas(conn)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO projects (project_id, title, aspect_ratio, target_width, target_height, "
                "duration_seconds, part_count, content_language, thumbnail_text_language, status, created_at, updated_at) "
                "VALUES (?, 'WAL Project', '9:16', 1080, 1920, 24.0, 3, 'en', 'en', 'active', datetime('now'), datetime('now'));",
                (pid,),
            )
            conn.commit()

        backup_path = Path(self.temp_dir) / "backup_test.db"
        result_path = create_consistent_backup(self.db_path, backup_path)

        self.assertTrue(result_path.exists())
        self.assertTrue(verify_database_integrity(result_path))

        # Assert data exists in backup file
        with sqlite3.connect(str(result_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT title FROM projects WHERE project_id = ?;", (pid,))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[0], "WAL Project")

    def test_crash_safe_coordinated_quarantine(self):
        """Verify coordinated quarantine moves main DB and active sidecars (-wal, -shm)."""
        init_database_tables(self.db_path)

        # Create active sidecars
        wal_file = Path(str(self.db_path) + "-wal")
        shm_file = Path(str(self.db_path) + "-shm")
        wal_file.write_text("wal_data")
        shm_file.write_text("shm_data")

        quarantines_dir = Path(self.temp_dir) / "quarantines"
        quarantine_result = quarantine_database_and_sidecars(self.db_path, quarantines_dir)

        self.assertTrue(quarantine_result.exists())
        self.assertFalse(quarantine_result.name.endswith(".in_progress"))
        self.assertTrue((quarantine_result / self.db_path.name).exists())
        self.assertTrue((quarantine_result / wal_file.name).exists())
        self.assertTrue((quarantine_result / shm_file.name).exists())

        # Assert files in original location were completely cleared
        self.assertFalse(self.db_path.exists())
        self.assertFalse(wal_file.exists())
        self.assertFalse(shm_file.exists())

    def test_interrupted_quarantine_startup_fail_closed(self):
        """Startup strictly prohibits auto-cleanup when *.in_progress quarantine is found."""
        quarantines_dir = Path(self.temp_dir) / "quarantines"
        quarantines_dir.mkdir(parents=True, exist_ok=True)
        in_prog = quarantines_dir / "quarantine_9999.in_progress"
        in_prog.mkdir(parents=True, exist_ok=True)
        (in_prog / "sample.db").write_text("partial_data")

        # Startup inspection must raise MigrationStateAmbiguousError
        with self.assertRaises(MigrationStateAmbiguousError) as ctx:
            inspect_migration_state_on_startup(self.db_path, quarantines_dir=quarantines_dir)

        self.assertIn("STARTUP HALTED", str(ctx.exception))
        self.assertIn("Automatic cleanup, deletion, or restore is strictly prohibited", str(ctx.exception))

        # Assert staging directory was preserved intact
        self.assertTrue(in_prog.exists())
        self.assertTrue((in_prog / "sample.db").exists())

    def test_migration_downgrade_and_upgrade(self):
        """Test clean schema teardown and recreation via downgrade and upgrade."""
        init_database_tables(self.db_path)
        self.assertTrue(self.db_path.exists())

        # Downgrade to base
        run_migrations_downgrade(self.db_path, target_revision="base")

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [r[0] for r in cursor.fetchall() if not r[0].startswith("sqlite_")]
            self.assertEqual(len(tables), 0)

        # Upgrade re-creates schema cleanly
        run_migrations_upgrade(self.db_path)

        with sqlite3.connect(str(self.db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables2 = {r[0] for r in cursor.fetchall() if not r[0].startswith("sqlite_")}
            self.assertEqual(len(tables2), 7)


if __name__ == "__main__":
    unittest.main()
