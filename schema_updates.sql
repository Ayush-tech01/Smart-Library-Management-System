-- =============================================
-- LMS Enhanced Schema - MySQL 8.0 Compatible
-- Run once on your library_management database
-- =============================================
USE library_management;

-- 1. Extra columns for books (safe - using stored procedure)
DROP PROCEDURE IF EXISTS lms_migrate;
DELIMITER $$
CREATE PROCEDURE lms_migrate()
BEGIN
    -- books: cover_url
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='books' AND COLUMN_NAME='cover_url') THEN
        ALTER TABLE books ADD COLUMN cover_url VARCHAR(500) NULL;
    END IF;
    -- books: description
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='books' AND COLUMN_NAME='description') THEN
        ALTER TABLE books ADD COLUMN description TEXT NULL;
    END IF;
    -- books: language
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='books' AND COLUMN_NAME='language') THEN
        ALTER TABLE books ADD COLUMN language VARCHAR(50) DEFAULT 'English';
    END IF;
    -- books: pages
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='books' AND COLUMN_NAME='pages') THEN
        ALTER TABLE books ADD COLUMN pages INT NULL;
    END IF;
    -- books: shelf_location
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='books' AND COLUMN_NAME='shelf_location') THEN
        ALTER TABLE books ADD COLUMN shelf_location VARCHAR(50) NULL;
    END IF;
    -- transactions: fine_paid
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='transactions' AND COLUMN_NAME='fine_paid') THEN
        ALTER TABLE transactions ADD COLUMN fine_paid BOOLEAN DEFAULT FALSE;
    END IF;
    -- transactions: payment_method
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='transactions' AND COLUMN_NAME='payment_method') THEN
        ALTER TABLE transactions ADD COLUMN payment_method ENUM('cash','online','waived') NULL;
    END IF;
END$$
DELIMITER ;
CALL lms_migrate();
DROP PROCEDURE IF EXISTS lms_migrate;

-- 2. Users table (unified auth: admin / librarian / member)
CREATE TABLE IF NOT EXISTS users (
    id           INT PRIMARY KEY AUTO_INCREMENT,
    name         VARCHAR(100) NOT NULL,
    email        VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role         ENUM('admin','librarian','member') DEFAULT 'member',
    member_id    INT NULL,
    avatar_color VARCHAR(7) DEFAULT '#8b5cf6',
    is_active    BOOLEAN DEFAULT TRUE,
    last_login   DATETIME NULL,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE SET NULL
);

-- 3. Book reviews & star ratings
CREATE TABLE IF NOT EXISTS reviews (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    book_id     INT NOT NULL,
    user_id     INT NOT NULL,
    rating      TINYINT NOT NULL,
    review_text TEXT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_review (book_id, user_id),
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 4. Reservations queue
CREATE TABLE IF NOT EXISTS reservations (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    book_id     INT NOT NULL,
    user_id     INT NOT NULL,
    member_id   INT NOT NULL,
    status      ENUM('pending','ready','fulfilled','cancelled') DEFAULT 'pending',
    reserved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notified_at DATETIME NULL,
    FOREIGN KEY (book_id)   REFERENCES books(id)   ON DELETE CASCADE,
    FOREIGN KEY (user_id)   REFERENCES users(id)   ON DELETE CASCADE,
    FOREIGN KEY (member_id) REFERENCES members(id) ON DELETE CASCADE
);

-- 5. Wishlist
CREATE TABLE IF NOT EXISTS wishlist (
    id       INT PRIMARY KEY AUTO_INCREMENT,
    user_id  INT NOT NULL,
    book_id  INT NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_wishlist (user_id, book_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE
);

-- 6. Notifications
CREATE TABLE IF NOT EXISTS notifications (
    id         INT PRIMARY KEY AUTO_INCREMENT,
    user_id    INT NOT NULL,
    title      VARCHAR(200) NOT NULL,
    message    TEXT NOT NULL,
    type       ENUM('info','warning','success','danger') DEFAULT 'info',
    is_read    BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 7. Book requests (members request catalog additions)
CREATE TABLE IF NOT EXISTS book_requests (
    id         INT PRIMARY KEY AUTO_INCREMENT,
    user_id    INT NOT NULL,
    title      VARCHAR(200) NOT NULL,
    author     VARCHAR(100) NULL,
    isbn       VARCHAR(20)  NULL,
    reason     TEXT NULL,
    status     ENUM('pending','approved','rejected','fulfilled') DEFAULT 'pending',
    admin_note TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 8. Fine payments ledger
CREATE TABLE IF NOT EXISTS fine_payments (
    id             INT PRIMARY KEY AUTO_INCREMENT,
    transaction_id INT NOT NULL,
    amount         DECIMAL(10,2) NOT NULL,
    payment_date   DATE NOT NULL,
    method         ENUM('cash','online','waived') DEFAULT 'cash',
    received_by    INT NULL,
    notes          TEXT NULL,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    FOREIGN KEY (received_by)   REFERENCES users(id)         ON DELETE SET NULL
);

-- Default admin auto-seeded by Flask app on first run (admin@library.com / Admin@2024)
