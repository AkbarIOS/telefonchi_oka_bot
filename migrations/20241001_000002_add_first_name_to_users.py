"""
Migration: Add first_name column to users table
Created: 2024-10-01 00:00:02
"""

async def up(db):
    """Run the migration"""
    await db.execute("ALTER TABLE users ADD COLUMN first_name VARCHAR(100) DEFAULT 'Unknown'")


async def down(db):
    """Rollback the migration"""
    await db.execute("ALTER TABLE users DROP COLUMN first_name")