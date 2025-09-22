# Database Migrations

This directory contains database migration files for the Telefonchi Bot project. Migrations ensure that database schema changes are tracked, versioned, and reproducible across different environments.

## Migration System

Our migration system is similar to Laravel/Django migrations, providing:
- **Version Control**: All schema changes are tracked in version control
- **Reproducibility**: Database setup is identical across environments
- **Rollback Support**: Ability to undo schema changes
- **Team Collaboration**: No more manual SQL scripts

## File Structure

```
migrations/
├── README.md                                           # This file
├── 20241001_000001_create_initial_schema.py           # Initial database schema
├── 20241001_000002_add_first_name_to_users.py         # Add first_name column
├── 20241001_000003_add_city_and_contact_phone_to_advertisements.py  # Add city & contact_phone
└── ... (future migrations)
```

## Migration File Format

Each migration file has a timestamp prefix and descriptive name:
- Format: `YYYYMMDD_HHMMSS_description.py`
- Example: `20241001_120000_add_email_to_users.py`

## Migration Commands

### Run All Pending Migrations
```bash
python migrate.py migrate
```

### Check Migration Status
```bash
python migrate.py status
```

### Create New Migration
```bash
python migrate.py create add_new_column
```

### Rollback Last Migration
```bash
python migrate.py rollback
```

### Rollback Multiple Migrations
```bash
python migrate.py rollback 3
```

## Migration File Structure

Each migration file must have both `up()` and `down()` functions:

```python
"""
Migration: Description of what this migration does
Created: 2024-10-01 12:00:00
"""

async def up(db):
    """Run the migration"""
    await db.execute("ALTER TABLE users ADD COLUMN email VARCHAR(255)")

async def down(db):
    """Rollback the migration"""
    await db.execute("ALTER TABLE users DROP COLUMN email")
```

## Deployment Instructions

### Fresh Installation (New Project Copy)

1. **Clone the repository**
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Set up environment variables** (copy from existing deployment)
4. **Run migrations**: `python migrate.py migrate`

This will create all tables and apply all schema changes automatically.

### Existing Installation Updates

When you pull new code with new migrations:

1. **Pull latest code**: `git pull`
2. **Check migration status**: `python migrate.py status`
3. **Run pending migrations**: `python migrate.py migrate`

## Railway Deployment

For Railway deployments, migrations should be run automatically. Add this to your Railway deployment script or run manually:

```bash
# After code deployment
python migrate.py migrate
```

## Best Practices

1. **Never edit existing migrations** - Create new ones instead
2. **Always test migrations** on development first
3. **Write reversible migrations** - Ensure `down()` function works
4. **Use descriptive names** for migration files
5. **Backup database** before running migrations in production

## Migration Examples

### Adding a Column
```python
async def up(db):
    await db.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20)")

async def down(db):
    await db.execute("ALTER TABLE users DROP COLUMN phone")
```

### Creating a Table
```python
async def up(db):
    await db.execute("""
        CREATE TABLE notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

async def down(db):
    await db.execute("DROP TABLE notifications")
```

### Adding an Index
```python
async def up(db):
    await db.execute("CREATE INDEX idx_users_telegram_id ON users(telegram_id)")

async def down(db):
    await db.execute("DROP INDEX idx_users_telegram_id ON users")
```

## Troubleshooting

### Migration Fails
1. Check the error message
2. Verify database connection
3. Check if the migration SQL is valid
4. Ensure foreign key constraints are satisfied

### Migration Already Applied
The system tracks which migrations have been run, so re-running is safe.

### Rollback Issues
Make sure your `down()` function is correct and reversible.

## Current Schema Changes Tracked

1. **20241001_000001_create_initial_schema.py**
   - Creates all initial tables (users, categories, brands, advertisements, favorites)
   - Adds sample data for categories and brands

2. **20241001_000002_add_first_name_to_users.py**
   - Adds `first_name` column to users table

3. **20241001_000003_add_city_and_contact_phone_to_advertisements.py**
   - Adds `city` and `contact_phone` columns to advertisements table

## Migration Table

The system automatically creates a `migrations` table to track which migrations have been applied:

```sql
CREATE TABLE migrations (
    id INT AUTO_INCREMENT PRIMARY KEY,
    migration VARCHAR(255) NOT NULL UNIQUE,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

This ensures migrations are only run once and in the correct order.