-- Add analysis_type column to analysis_tasks table
ALTER TABLE analysis_tasks ADD COLUMN IF NOT EXISTS analysis_type VARCHAR(10) DEFAULT 'fast';

-- Add analysis_type column to reports table
ALTER TABLE reports ADD COLUMN IF NOT EXISTS analysis_type VARCHAR(10) DEFAULT 'fast';

-- Update existing records to set default value "fast"
UPDATE analysis_tasks SET analysis_type = 'fast' WHERE analysis_type IS NULL;
UPDATE reports SET analysis_type = 'fast' WHERE analysis_type IS NULL; 