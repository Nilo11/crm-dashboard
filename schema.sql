CREATE DATABASE IF NOT EXISTS crm_db;
USE crm_db;

CREATE TABLE IF NOT EXISTS leads (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    company VARCHAR(100),
    status ENUM('New', 'Contacted', 'Qualified', 'Closed') DEFAULT 'New',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO leads (name, email, phone, company, status) VALUES 
('Swara Patil', 'swara@techcorp.com', '+91 7788445566', 'TechCorp', 'New'),
('Sarah Khan', 'sarah@innovate.io', '+91 9876543210', 'Innovate Labs', 'Contacted');