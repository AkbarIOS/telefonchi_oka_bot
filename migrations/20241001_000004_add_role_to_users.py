"""
Migration: Add role column to users table
Created: 2024-10-01 00:00:04
"""

async def up(db):
    """Run the migration"""
    await db.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'")

async def down(db):
    """Rollback the migration"""
    await db.execute("ALTER TABLE users DROP COLUMN role")