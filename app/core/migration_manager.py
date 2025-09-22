"""
Database Migration Manager

This module provides a simple migration system similar to Laravel/Django migrations.
Migrations are versioned and tracked to ensure database schema consistency.
"""

import os
import importlib.util
import logging
from datetime import datetime
from typing import List, Dict, Any
from app.repositories.database import Database

logger = logging.getLogger(__name__)


class MigrationManager:
    """Handles database migrations"""

    def __init__(self, database: Database, migrations_dir: str = "migrations"):
        self.db = database
        self.migrations_dir = migrations_dir
        self.base_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), migrations_dir)

    async def initialize_migration_table(self):
        """Create migrations table if it doesn't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS migrations (
            id INT AUTO_INCREMENT PRIMARY KEY,
            migration VARCHAR(255) NOT NULL UNIQUE,
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
        await self.db.execute(create_table_query)
        logger.info("Migration table initialized")

    async def get_executed_migrations(self) -> List[str]:
        """Get list of executed migrations"""
        try:
            result = await self.db.fetchall("SELECT migration FROM migrations ORDER BY executed_at")
            return [row['migration'] for row in result]
        except Exception as e:
            logger.warning(f"Could not fetch executed migrations: {e}")
            return []

    def get_available_migrations(self) -> List[str]:
        """Get list of available migration files"""
        if not os.path.exists(self.base_path):
            return []

        migrations = []
        for filename in os.listdir(self.base_path):
            if filename.endswith('.py') and filename != '__init__.py':
                migrations.append(filename[:-3])  # Remove .py extension

        return sorted(migrations)

    def load_migration(self, migration_name: str):
        """Load a migration module"""
        migration_path = os.path.join(self.base_path, f"{migration_name}.py")

        if not os.path.exists(migration_path):
            raise FileNotFoundError(f"Migration file not found: {migration_path}")

        spec = importlib.util.spec_from_file_location(migration_name, migration_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        return module

    async def run_migration(self, migration_name: str):
        """Execute a single migration"""
        logger.info(f"Running migration: {migration_name}")

        try:
            migration_module = self.load_migration(migration_name)

            # Execute the up() function
            if hasattr(migration_module, 'up'):
                await migration_module.up(self.db)

                # Record migration as executed
                await self.db.execute(
                    "INSERT INTO migrations (migration) VALUES (%s)",
                    [migration_name]
                )

                logger.info(f"Migration {migration_name} executed successfully")
            else:
                raise AttributeError(f"Migration {migration_name} has no 'up' function")

        except Exception as e:
            logger.error(f"Migration {migration_name} failed: {e}")
            raise

    async def rollback_migration(self, migration_name: str):
        """Rollback a single migration"""
        logger.info(f"Rolling back migration: {migration_name}")

        try:
            migration_module = self.load_migration(migration_name)

            # Execute the down() function
            if hasattr(migration_module, 'down'):
                await migration_module.down(self.db)

                # Remove migration from executed list
                await self.db.execute(
                    "DELETE FROM migrations WHERE migration = %s",
                    [migration_name]
                )

                logger.info(f"Migration {migration_name} rolled back successfully")
            else:
                raise AttributeError(f"Migration {migration_name} has no 'down' function")

        except Exception as e:
            logger.error(f"Rollback of {migration_name} failed: {e}")
            raise

    async def migrate(self):
        """Run all pending migrations"""
        await self.initialize_migration_table()

        executed_migrations = await self.get_executed_migrations()
        available_migrations = self.get_available_migrations()

        pending_migrations = [
            migration for migration in available_migrations
            if migration not in executed_migrations
        ]

        if not pending_migrations:
            logger.info("No pending migrations")
            return

        logger.info(f"Found {len(pending_migrations)} pending migrations")

        for migration in pending_migrations:
            await self.run_migration(migration)

        logger.info("All migrations completed successfully")

    async def rollback(self, steps: int = 1):
        """Rollback the last N migrations"""
        executed_migrations = await self.get_executed_migrations()

        if not executed_migrations:
            logger.info("No migrations to rollback")
            return

        migrations_to_rollback = executed_migrations[-steps:]
        migrations_to_rollback.reverse()  # Rollback in reverse order

        logger.info(f"Rolling back {len(migrations_to_rollback)} migrations")

        for migration in migrations_to_rollback:
            await self.rollback_migration(migration)

        logger.info("Rollback completed successfully")

    def create_migration(self, name: str) -> str:
        """Create a new migration file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        migration_name = f"{timestamp}_{name}"
        migration_path = os.path.join(self.base_path, f"{migration_name}.py")

        # Create migrations directory if it doesn't exist
        os.makedirs(self.base_path, exist_ok=True)

        # Migration template
        template = f'''"""
Migration: {name}
Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

async def up(db):
    """Run the migration"""
    # Add your migration code here
    # Example:
    # await db.execute("CREATE TABLE example (id INT PRIMARY KEY)")
    pass

async def down(db):
    """Rollback the migration"""
    # Add your rollback code here
    # Example:
    # await db.execute("DROP TABLE example")
    pass
'''

        with open(migration_path, 'w') as f:
            f.write(template)

        logger.info(f"Migration created: {migration_path}")
        return migration_name

    async def status(self) -> Dict[str, Any]:
        """Get migration status"""
        await self.initialize_migration_table()

        executed_migrations = await self.get_executed_migrations()
        available_migrations = self.get_available_migrations()
        pending_migrations = [
            migration for migration in available_migrations
            if migration not in executed_migrations
        ]

        return {
            "executed": executed_migrations,
            "pending": pending_migrations,
            "total_available": len(available_migrations),
            "total_executed": len(executed_migrations),
            "total_pending": len(pending_migrations)
        }