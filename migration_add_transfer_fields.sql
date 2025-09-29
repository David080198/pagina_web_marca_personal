-- Migration: Add transfer fields to Payment model
-- Date: 2025-09-28

-- Add new columns to payment table
ALTER TABLE payment ADD COLUMN transfer_sender_name VARCHAR(100);
ALTER TABLE payment ADD COLUMN transfer_reference VARCHAR(100);
ALTER TABLE payment ADD COLUMN transfer_amount FLOAT;
ALTER TABLE payment ADD COLUMN payment_receipt_path VARCHAR(255);
ALTER TABLE payment ADD COLUMN additional_notes TEXT;
ALTER TABLE payment ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Update the updated_at column to auto-update on changes
-- Note: PostgreSQL doesn't have ON UPDATE CURRENT_TIMESTAMP like MySQL
-- We'll handle this in the application code
