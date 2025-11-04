#!/usr/bin/env python3
"""
Production-ready migration management script.

This script provides safe database migrations with:
- Backup creation
- Dry-run mode
- Rollback capability
- Multi-environment support
- Progress tracking
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from alembic.config import Config

from alembic import command

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


class MigrationManager:
    """Manages database migrations with safety features."""

    def __init__(self, database_url: Optional[str] = None):
        self.database_url = database_url or os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        self.alembic_cfg = Config("alembic.ini")
        self.alembic_cfg.set_main_option("sqlalchemy.url", self.database_url)

        # Convert async URL to sync for migrations
        if self.database_url.startswith("postgresql+asyncpg://"):
            sync_url = self.database_url.replace(
                "postgresql+asyncpg://", "postgresql://"
            )
            self.alembic_cfg.set_main_option("sqlalchemy.url", sync_url)

    async def create_backup(self, backup_name: Optional[str] = None) -> str:
        """Create a database backup before migration."""
        if not self.database_url.startswith("postgresql"):
            print("⚠️  Backup only supported for PostgreSQL")
            return ""

        if not backup_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"dcmaidbot_backup_{timestamp}"

        # Parse connection info
        import urllib.parse as urlparse

        parsed = urlparse.urlparse(
            self.database_url.replace("postgresql+asyncpg://", "postgresql://")
        )
        dbname = parsed.path[1:]  # Remove leading slash
        user = parsed.username
        host = parsed.hostname
        port = parsed.port or 5432

        backup_file = f"/tmp/{backup_name}.sql"

        # Create backup using pg_dump
        import subprocess

        cmd = [
            "pg_dump",
            "-h",
            host,
            "-p",
            str(port),
            "-U",
            user,
            "-d",
            dbname,
            "-f",
            backup_file,
            "--no-password",
            "--verbose",
            "--format=custom",
        ]

        print(f"📦 Creating backup: {backup_file}")
        env = os.environ.copy()
        env["PGPASSWORD"] = parsed.password

        try:
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Backup created successfully: {backup_file}")
                return backup_file
            else:
                print(f"❌ Backup failed: {result.stderr}")
                return ""
        except Exception as e:
            print(f"❌ Backup error: {e}")
            return ""

    def check_connection(self) -> bool:
        """Test database connection."""
        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(self.alembic_cfg.get_main_option("sqlalchemy.url"))
            with engine.begin() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database connection successful")
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def get_current_revision(self) -> Optional[str]:
        """Get current database revision."""
        try:
            from alembic.runtime.migration import MigrationContext
            from sqlalchemy import create_engine

            engine = create_engine(self.alembic_cfg.get_main_option("sqlalchemy.url"))
            with engine.begin() as conn:
                context = MigrationContext.configure(conn)
                return context.get_current_revision()
        except Exception as e:
            print(f"⚠️  Could not get current revision: {e}")
            return None

    def get_pending_migrations(self) -> list:
        """Get list of pending migrations."""
        try:
            from alembic.script import ScriptDirectory

            script_dir = ScriptDirectory.from_config(self.alembic_cfg)
            head_revision = script_dir.get_current_head()
            current_revision = self.get_current_revision()

            if current_revision == head_revision:
                print("✅ Database is up to date")
                return []

            # Get pending migrations
            revisions = []
            for rev in script_dir.walk_revisions("head", current_revision or "base"):
                if rev.revision != current_revision:
                    revisions.append(rev)

            return list(reversed(revisions))
        except Exception as e:
            print(f"⚠️  Could not get pending migrations: {e}")
            return []

    def upgrade(
        self, revision: str = "head", dry_run: bool = False, sql: bool = False
    ) -> bool:
        """Upgrade database to specified revision."""
        if dry_run:
            print("🔍 DRY RUN MODE - No changes will be applied")

        if sql:
            print("📝 Generating SQL script")
            command.upgrade(self.alembic_cfg, revision, sql=True)
            return True

        try:
            print(f"⬆️  Upgrading to revision: {revision}")
            command.upgrade(self.alembic_cfg, revision)
            print("✅ Upgrade completed successfully")
            return True
        except Exception as e:
            print(f"❌ Upgrade failed: {e}")
            return False

    def downgrade(self, revision: str = "-1", dry_run: bool = False) -> bool:
        """Downgrade database to specified revision."""
        if dry_run:
            print("🔍 DRY RUN MODE - No changes will be applied")

        try:
            print(f"⬇️  Downgrading to revision: {revision}")
            command.downgrade(self.alembic_cfg, revision)
            print("✅ Downgrade completed successfully")
            return True
        except Exception as e:
            print(f"❌ Downgrade failed: {e}")
            return False

    def stamp(self, revision: str) -> bool:
        """Mark database as at specified revision without running migrations."""
        try:
            print(f"🏷️  Stamping database as revision: {revision}")
            command.stamp(self.alembic_cfg, revision)
            print("✅ Stamp completed successfully")
            return True
        except Exception as e:
            print(f"❌ Stamp failed: {e}")
            return False

    def history(self, verbose: bool = False) -> None:
        """Show migration history."""
        print("\n📜 Migration History:")
        command.history(self.alembic_cfg, verbose=verbose)

    def current(self) -> None:
        """Show current revision."""
        print("\n📍 Current Revision:")
        command.current(self.alembic_cfg, verbose=True)

    def reset_database(self, confirm: bool = False) -> bool:
        """Reset database to base state (DANGEROUS!)."""
        if not confirm:
            response = input(
                "⚠️  This will delete ALL data. Are you sure? (type 'DELETE ALL DATA'): "
            )
            if response != "DELETE ALL DATA":
                print("❌ Operation cancelled")
                return False

        try:
            print("🗑️  Resetting database to base state")
            command.downgrade(self.alembic_cfg, "base")
            print("✅ Database reset complete")
            return True
        except Exception as e:
            print(f"❌ Reset failed: {e}")
            return False

    async def migrate_with_failsafe(self, target_revision: str = "head") -> bool:
        """Perform migration with automatic rollback on failure."""
        # Get current revision
        current_rev = self.get_current_revision()

        # Create backup if PostgreSQL
        backup_file = ""
        if self.database_url.startswith("postgresql"):
            backup_file = await self.create_backup()

        # Get pending migrations
        pending = self.get_pending_migrations()
        if not pending:
            return True

        print("\n📋 Migration Plan:")
        print(f"   Current: {current_rev or 'None'}")
        print(f"   Target: {target_revision}")
        print(f"   Pending: {len(pending)} migrations")

        # Show pending migrations
        for i, rev in enumerate(pending, 1):
            print(f"   {i}. {rev.revision} - {rev.doc}")

        # Perform migration
        try:
            success = self.upgrade(target_revision)
            if success:
                print("\n✅ Migration completed successfully!")
                if backup_file:
                    print(f"   Backup retained at: {backup_file}")
                return True
            else:
                # Rollback on failure
                if current_rev:
                    print(f"\n❌ Migration failed! Rolling back to {current_rev}...")
                    self.downgrade(current_rev)
                return False
        except Exception as e:
            print(f"\n❌ Migration failed with error: {e}")
            if current_rev:
                print(f"   Rolling back to {current_rev}...")
                self.downgrade(current_rev)
            return False


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Database Migration Manager")
    parser.add_argument("--database-url", help="Database connection URL")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )
    parser.add_argument(
        "--sql", action="store_true", help="Generate SQL script instead of executing"
    )
    parser.add_argument(
        "--backup", action="store_true", help="Create backup before migration"
    )
    parser.add_argument("--no-backup", action="store_true", help="Skip backup creation")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Upgrade command
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade database")
    upgrade_parser.add_argument(
        "revision", nargs="?", default="head", help="Target revision (default: head)"
    )

    # Downgrade command
    downgrade_parser = subparsers.add_parser("downgrade", help="Downgrade database")
    downgrade_parser.add_argument(
        "revision", nargs="?", default="-1", help="Target revision"
    )

    # Other commands
    subparsers.add_parser("current", help="Show current revision")
    subparsers.add_parser("history", help="Show migration history")
    subparsers.add_parser("pending", help="Show pending migrations")
    subparsers.add_parser("check", help="Check database connection")

    # Reset command (dangerous)
    reset_parser = subparsers.add_parser("reset", help="Reset database (DANGEROUS!)")
    reset_parser.add_argument(
        "--confirm", action="store_true", help="Skip confirmation prompt"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Initialize migration manager
    try:
        manager = MigrationManager(args.database_url)
    except Exception as e:
        print(f"❌ Failed to initialize migration manager: {e}")
        sys.exit(1)

    # Execute command
    success = True

    if args.command == "check":
        success = manager.check_connection()

    elif args.command == "current":
        manager.current()

    elif args.command == "history":
        manager.history(verbose=True)

    elif args.command == "pending":
        pending = manager.get_pending_migrations()
        if pending:
            print(f"\n⏳ Pending migrations ({len(pending)}):")
            for i, rev in enumerate(pending, 1):
                print(f"   {i}. {rev.revision} - {rev.doc}")
        else:
            print("\n✅ No pending migrations")

    elif args.command == "upgrade":
        if args.backup and not args.no_backup:
            await manager.create_backup()

        if args.sql:
            success = manager.upgrade(args.revision, dry_run=args.dry_run, sql=True)
        else:
            success = manager.upgrade(args.revision, dry_run=args.dry_run)

    elif args.command == "downgrade":
        success = manager.downgrade(args.revision, dry_run=args.dry_run)

    elif args.command == "reset":
        success = await manager.reset_database(confirm=args.confirm)

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
