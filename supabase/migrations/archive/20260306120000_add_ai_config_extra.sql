-- Add extra_config JSONB column for provider-specific fields
-- e.g. api_version for Azure, aws_region for Bedrock, vertex_project/location for Vertex AI
ALTER TABLE vaktram.user_ai_configs ADD COLUMN IF NOT EXISTS extra_config JSONB DEFAULT '{}'::jsonb;
