-- Create database if not exists
CREATE DATABASE IF NOT EXISTS qr_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE qr_system;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_username (username),
    INDEX idx_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Scan records table
CREATE TABLE IF NOT EXISTS scan_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    qr_content TEXT NOT NULL,
    scan_source VARCHAR(50) DEFAULT 'scanner',
    user_id INT,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    printed_at TIMESTAMP NULL,
    print_status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_scanned_at (scanned_at),
    INDEX idx_user_id (user_id),
    INDEX idx_print_status (print_status),
    FULLTEXT idx_qr_content (qr_content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Printers table
CREATE TABLE IF NOT EXISTS printers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    connection_type VARCHAR(50) NOT NULL,
    ip_address VARCHAR(45),
    port INT,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_connection_type (connection_type),
    INDEX idx_is_default (is_default),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default admin user (password: admin123)
INSERT INTO users (username, email, hashed_password, is_active) 
VALUES ('admin', 'admin@qr-system.local', '$2b$12$YourHashedPasswordHere', TRUE)
ON DUPLICATE KEY UPDATE username = username;

-- Insert default browser printer
INSERT INTO printers (name, connection_type, is_default, is_active)
VALUES ('Browser Printer', 'browser', TRUE, TRUE)
ON DUPLICATE KEY UPDATE name = name;