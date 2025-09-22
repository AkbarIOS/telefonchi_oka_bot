"""
Migration: Create initial database schema
Created: 2024-10-01 00:00:01
"""

async def up(db):
    """Run the migration"""

    # Create categories table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name_ru VARCHAR(100) NOT NULL,
            name_uz VARCHAR(100) NOT NULL,
            name_en VARCHAR(100) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create brands table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS brands (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            category_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
        )
    """)

    # Create users table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            telegram_id BIGINT UNIQUE NOT NULL,
            username VARCHAR(100),
            language VARCHAR(10) DEFAULT 'ru',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )
    """)

    # Create advertisements table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS advertisements (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            category_id INT NOT NULL,
            brand_id INT NOT NULL,
            model VARCHAR(255) NOT NULL,
            price INT NOT NULL,
            description TEXT NOT NULL,
            phone VARCHAR(20) NOT NULL,
            photo_path VARCHAR(500),
            status ENUM('pending', 'approved', 'rejected') DEFAULT 'pending',
            rejection_reason TEXT,
            moderated_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
            FOREIGN KEY (brand_id) REFERENCES brands(id) ON DELETE CASCADE
        )
    """)

    # Create favorites table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS favorites (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            advertisement_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (advertisement_id) REFERENCES advertisements(id) ON DELETE CASCADE,
            UNIQUE KEY unique_favorite (user_id, advertisement_id)
        )
    """)

    # Insert sample categories
    await db.execute("""
        INSERT INTO categories (name_ru, name_uz, name_en) VALUES
        ('Смартфоны', 'Smartfonlar', 'smartphones'),
        ('Планшеты', 'Planshetlar', 'tablets'),
        ('Ноутбуки', 'Noutbuklar', 'laptops'),
        ('Наушники', 'Quloqchinlar', 'headphones'),
        ('Часы', 'Soatlar', 'watches')
        ON DUPLICATE KEY UPDATE name_ru=VALUES(name_ru)
    """)

    # Insert sample brands
    await db.execute("""
        INSERT INTO brands (name, category_id) VALUES
        ('Apple', 1), ('Samsung', 1), ('Xiaomi', 1), ('Huawei', 1),
        ('Apple', 2), ('Samsung', 2), ('Lenovo', 2),
        ('Apple', 3), ('Dell', 3), ('HP', 3), ('Lenovo', 3),
        ('Apple', 4), ('Sony', 4), ('JBL', 4), ('Bose', 4),
        ('Apple', 5), ('Samsung', 5), ('Garmin', 5), ('Fitbit', 5)
        ON DUPLICATE KEY UPDATE name=VALUES(name)
    """)


async def down(db):
    """Rollback the migration"""
    await db.execute("DROP TABLE IF EXISTS favorites")
    await db.execute("DROP TABLE IF EXISTS advertisements")
    await db.execute("DROP TABLE IF EXISTS brands")
    await db.execute("DROP TABLE IF EXISTS categories")
    await db.execute("DROP TABLE IF EXISTS users")