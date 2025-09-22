"""
Migration: Add city and contact_phone columns to advertisements table
Created: 2024-10-01 00:00:03
"""

async def up(db):
    """Run the migration"""
    await db.execute("ALTER TABLE advertisements ADD COLUMN city VARCHAR(100) NOT NULL DEFAULT 'Unknown'")
    await db.execute("ALTER TABLE advertisements ADD COLUMN contact_phone VARCHAR(20) NOT NULL DEFAULT ''")


async def down(db):
    """Rollback the migration"""
    await db.execute("ALTER TABLE advertisements DROP COLUMN contact_phone")
    await db.execute("ALTER TABLE advertisements DROP COLUMN city")