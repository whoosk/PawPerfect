import os

import mysql.connector


DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "pawperfect"),
}


def get_connection():
    return mysql.connector.connect(
        **DB_CONFIG,
        autocommit=False,
    )


def init_db():
    server_config = DB_CONFIG.copy()
    database = server_config.pop("database")

    server_connection = mysql.connector.connect(**server_config)
    server_cursor = server_connection.cursor()
    server_cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS `{database}` "
        "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    server_cursor.close()
    server_connection.close()

    conn = mysql.connector.connect(**DB_CONFIG, autocommit=False)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            fullname VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            phone VARCHAR(255) NOT NULL,
            role ENUM('user', 'admin') NOT NULL DEFAULT 'user'
        )
        """
    )
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'users'
          AND column_name = 'role'
        """
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            """
            ALTER TABLE users
            ADD COLUMN role ENUM('user', 'admin')
            NOT NULL DEFAULT 'user' AFTER phone
            """
        )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sender_id INT NOT NULL,
            receiver_id INT NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN NOT NULL DEFAULT FALSE,
            is_archived BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
        """
    )
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'messages'
          AND column_name = 'is_read'
        """
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "ALTER TABLE messages ADD COLUMN is_read BOOLEAN NOT NULL DEFAULT FALSE"
        )
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_schema = DATABASE()
          AND table_name = 'messages'
          AND column_name = 'is_archived'
        """
    )
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "ALTER TABLE messages ADD COLUMN is_archived BOOLEAN NOT NULL DEFAULT FALSE"
        )
    cursor.execute(
        """
        INSERT INTO users (fullname, email, password, phone, role)
        VALUES ('Administrator', 'admin@pawperfect.com', 'admin123', 'N/A', 'admin')
        ON DUPLICATE KEY UPDATE role='admin'
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS pets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            name VARCHAR(100) NOT NULL,
            breed VARCHAR(100) NOT NULL,
            gender VARCHAR(30) NOT NULL,
            age VARCHAR(50) NOT NULL,
            photo_path VARCHAR(500) DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            pet_id INT NOT NULL,
            service VARCHAR(100) NOT NULL,
            pet_size VARCHAR(50) NOT NULL,
            appointment_date VARCHAR(50) NOT NULL,
            appointment_time VARCHAR(20) NOT NULL,
            status ENUM('Pending','Paid','Confirmed','Completed','Cancelled')
                NOT NULL DEFAULT 'Pending',
            price VARCHAR(20) NOT NULL DEFAULT 'P0.00',
            payment_method VARCHAR(30) DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (pet_id) REFERENCES pets(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS notifications (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            appointment_id INT DEFAULT NULL,
            notification_type VARCHAR(30) NOT NULL,
            title VARCHAR(100) NOT NULL,
            message TEXT NOT NULL,
            is_read BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            setting_key VARCHAR(100) PRIMARY KEY,
            setting_value TEXT NOT NULL
        ) ENGINE=InnoDB
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INT NOT NULL,
            preference_key VARCHAR(100) NOT NULL,
            preference_value TEXT NOT NULL,
            PRIMARY KEY (user_id, preference_key),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        ) ENGINE=InnoDB
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS services (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            description TEXT NOT NULL,
            small_price DECIMAL(10, 2) NOT NULL,
            medium_price DECIMAL(10, 2) NOT NULL,
            large_price DECIMAL(10, 2) NOT NULL
        ) ENGINE=InnoDB
        """
    )
    cursor.executemany(
        """
        INSERT IGNORE INTO services
            (name, description, small_price, medium_price, large_price)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            ("Basic Bath", "Bath, shampoo and conditioning", 350, 450, 550),
            ("Full Grooming", "Bath, haircut and nail trimming", 350, 700, 850),
            ("Nail Trimming", "Trim nails for pet comfort", 100, 150, 150),
            ("Teeth Cleaning", "Brush and clean teeth", 100, 150, 150),
            ("Ear Cleaning", "Clean ears and prevent infection", 100, 150, 150),
            ("Premium Grooming", "Complete grooming package", 750, 900, 1000),
        ),
    )
    conn.commit()
    cursor.close()
    return conn
