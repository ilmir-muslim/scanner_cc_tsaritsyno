-- PostgreSQL initialization script for QR System

-- Create tables if they don't exist
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS scan_records (
    id SERIAL PRIMARY KEY,
    qr_content TEXT NOT NULL,
    scan_source VARCHAR(50) DEFAULT 'scanner',
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    scanned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    printed_at TIMESTAMP WITH TIME ZONE,
    print_status VARCHAR(20) DEFAULT 'pending' CHECK (print_status IN ('pending', 'success', 'failed'))
);

CREATE TABLE IF NOT EXISTS printers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    connection_type VARCHAR(50) NOT NULL CHECK (connection_type IN ('network', 'usb', 'bluetooth', 'browser')),
    ip_address VARCHAR(45),
    port INTEGER,
    is_default BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

CREATE INDEX IF NOT EXISTS idx_scan_records_scanned_at ON scan_records(scanned_at);
CREATE INDEX IF NOT EXISTS idx_scan_records_user_id ON scan_records(user_id);
CREATE INDEX IF NOT EXISTS idx_scan_records_print_status ON scan_records(print_status);
CREATE INDEX IF NOT EXISTS idx_scan_records_qr_content ON scan_records(qr_content);

CREATE INDEX IF NOT EXISTS idx_printers_name ON printers(name);
CREATE INDEX IF NOT EXISTS idx_printers_connection_type ON printers(connection_type);
CREATE INDEX IF NOT EXISTS idx_printers_is_default ON printers(is_default);
CREATE INDEX IF NOT EXISTS idx_printers_is_active ON printers(is_active);

-- Insert default data
INSERT INTO users (username, email, hashed_password, is_active) 
VALUES ('admin', 'admin@qr-system.local', '$2b$12$YourHashedPasswordHere', TRUE)
ON CONFLICT (username) DO NOTHING;

INSERT INTO printers (name, connection_type, is_default, is_active)
VALUES ('Browser Printer', 'browser', TRUE, TRUE)
ON CONFLICT (name) DO NOTHING;

-- Create a function to update printed_at timestamp
CREATE OR REPLACE FUNCTION update_printed_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.print_status = 'success' AND OLD.print_status != 'success' THEN
        NEW.printed_at = CURRENT_TIMESTAMP;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update printed_at
DROP TRIGGER IF EXISTS trigger_update_printed_at ON scan_records;
CREATE TRIGGER trigger_update_printed_at
    BEFORE UPDATE ON scan_records
    FOR EACH ROW
    EXECUTE FUNCTION update_printed_at();