#!/usr/bin/env python3
"""
Database Migration CLI Tool

Usage:
    python migrate.py migrate          # Run all pending migrations
    python migrate.py rollback [steps] # Rollback last N migrations (default: 1)
    python migrate.py status           # Show migration status
    python migrate.py create <name>    # Create a new migration file
"""

import asyncio
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.migration_manager import MigrationManager
from app.repositories.database import Database
from app.core.config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1]

    # Initialize database and migration manager
    db = Database()
    await db.initialize()
    migration_manager = MigrationManager(db)

    try:
        if command == "migrate":
            await migration_manager.migrate()

        elif command == "rollback":
            steps = int(sys.argv[2]) if len(sys.argv) > 2 else 1
            await migration_manager.rollback(steps)

        elif command == "status":
            status = await migration_manager.status()
            print("\n=== Migration Status ===")
            print(f"Total available: {status['total_available']}")
            print(f"Total executed: {status['total_executed']}")
            print(f"Total pending: {status['total_pending']}")

            if status['executed']:
                print("\nExecuted migrations:")
                for migration in status['executed']:
                    print(f"  ✅ {migration}")

            if status['pending']:
                print("\nPending migrations:")
                for migration in status['pending']:
                    print(f"  ⏳ {migration}")

            if not status['pending']:
                print("\n✅ All migrations are up to date!")

        elif command == "create":
            if len(sys.argv) < 3:
                print("Usage: python migrate.py create <migration_name>")
                return

            migration_name = sys.argv[2]
            created_migration = migration_manager.create_migration(migration_name)
            print(f"Created migration: {created_migration}")

        else:
            print(f"Unknown command: {command}")
            print(__doc__)

    except Exception as e:
        logger.error(f"Migration command failed: {e}")
        raise
    finally:
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())