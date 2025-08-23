-- Migration: Add contract metadata fields
-- Purpose: Support proper contract lifecycle management

-- Add missing columns to pilot_contracts if they don't exist
ALTER TABLE pilot_contracts 
ADD COLUMN IF NOT EXISTS file_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS file_size INTEGER,
ADD COLUMN IF NOT EXISTS file_content BYTEA,
ADD COLUMN IF NOT EXISTS mime_type VARCHAR(100),
ADD COLUMN IF NOT EXISTS parsing_status VARCHAR(20) DEFAULT 'pending',
ADD COLUMN IF NOT EXISTS parsed_data JSONB,
ADD COLUMN IF NOT EXISTS error_message TEXT;

-- Add index for active contract lookup
CREATE INDEX IF NOT EXISTS idx_pilot_contracts_airline_active 
ON pilot_contracts(airline, status) 
WHERE status = 'active';

-- Add index for date-based queries
CREATE INDEX IF NOT EXISTS idx_pilot_contracts_dates 
ON pilot_contracts(airline, effective_date, expiration_date);

-- Create a function to ensure only one active contract per airline
CREATE OR REPLACE FUNCTION ensure_single_active_contract()
RETURNS TRIGGER AS $$
BEGIN
    -- If setting a contract as active
    IF NEW.status = 'active' THEN
        -- Deactivate all other contracts for this airline
        UPDATE pilot_contracts 
        SET status = 'deprecated',
            metadata = jsonb_set(
                COALESCE(metadata, '{}'::jsonb),
                '{deactivated_at}',
                to_jsonb(CURRENT_TIMESTAMP)
            )
        WHERE airline = NEW.airline 
        AND id != NEW.id 
        AND status = 'active';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for active contract management
DROP TRIGGER IF EXISTS trigger_ensure_single_active_contract ON pilot_contracts;
CREATE TRIGGER trigger_ensure_single_active_contract
BEFORE INSERT OR UPDATE ON pilot_contracts
FOR EACH ROW
EXECUTE FUNCTION ensure_single_active_contract();

-- Add audit columns if missing
ALTER TABLE pilot_contracts
ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id),
ADD COLUMN IF NOT EXISTS updated_by UUID REFERENCES users(id),
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES users(id);

-- Update existing records to have proper metadata structure
UPDATE pilot_contracts 
SET metadata = COALESCE(metadata, '{}'::jsonb) || 
    jsonb_build_object(
        'is_active', CASE WHEN status = 'active' THEN true ELSE false END,
        'migration_applied', CURRENT_TIMESTAMP
    )
WHERE metadata IS NULL OR NOT (metadata ? 'is_active');

-- Add comment explaining the metadata structure
COMMENT ON COLUMN pilot_contracts.metadata IS 
'JSON metadata including:
- is_active: boolean indicating if this is the current active contract
- effective_date: contract start date
- expiration_date: contract end date
- uploaded_by_email: email of uploader
- admin_notes: notes from admin
- processing_stats: extraction statistics
- deactivated_at: when contract was deactivated';

-- Create view for active contracts
CREATE OR REPLACE VIEW active_contracts AS
SELECT 
    pc.*,
    (metadata->>'is_active')::boolean as is_currently_active,
    (metadata->>'effective_date')::date as contract_start_date,
    (metadata->>'expiration_date')::date as contract_end_date,
    u.email as uploaded_by_email,
    u.first_name || ' ' || u.last_name as uploaded_by_name
FROM pilot_contracts pc
LEFT JOIN users u ON pc.uploaded_by = u.id
WHERE pc.status = 'active' 
   OR (pc.metadata->>'is_active')::boolean = true;

-- Grant appropriate permissions
GRANT SELECT ON active_contracts TO PUBLIC;
GRANT ALL ON pilot_contracts TO authenticated;

-- Add check constraint for date validity
ALTER TABLE pilot_contracts
ADD CONSTRAINT check_contract_dates 
CHECK (
    effective_date IS NULL 
    OR expiration_date IS NULL 
    OR effective_date < expiration_date
);