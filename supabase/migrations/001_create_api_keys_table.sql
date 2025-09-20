-- Create api_keys table for secure storage of user API keys
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id TEXT NOT NULL,
    platform TEXT NOT NULL,
    encrypted_api_key TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, platform)
);

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_api_keys_user_platform ON api_keys(user_id, platform);

-- Enable Row Level Security
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

-- Create policy to allow users to manage their own API keys
CREATE POLICY "Users can manage their own API keys" ON api_keys
    FOR ALL USING (auth.uid()::text = user_id);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_api_keys_updated_at 
    BEFORE UPDATE ON api_keys 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();
