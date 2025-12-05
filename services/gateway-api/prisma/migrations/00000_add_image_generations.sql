-- Migration: Add image_generations table
-- Agent 37: AI Image Generation tracking

CREATE TABLE IF NOT EXISTS image_generations (
    generation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Generation details
    prompt TEXT NOT NULL,
    provider VARCHAR(50) NOT NULL,  -- flux_pro, flux_dev, dalle3, etc.
    aspect_ratio VARCHAR(20),       -- 1:1, 9:16, etc.
    style VARCHAR(50),              -- photorealistic, cinematic, etc.
    quality VARCHAR(20),            -- low, medium, high

    -- Output
    image_path TEXT NOT NULL,

    -- Metadata
    cost_estimate DECIMAL(10, 4) DEFAULT 0.0,
    generation_time DECIMAL(10, 2) DEFAULT 0.0,
    generation_type VARCHAR(50),    -- product_shot, lifestyle, thumbnail
    platform VARCHAR(50),           -- instagram, youtube, etc.

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_image_generations_provider ON image_generations(provider);
CREATE INDEX idx_image_generations_type ON image_generations(generation_type);
CREATE INDEX idx_image_generations_created ON image_generations(created_at DESC);
CREATE INDEX idx_image_generations_platform ON image_generations(platform);

-- Comments
COMMENT ON TABLE image_generations IS 'AI-generated images for ad creatives (Agent 37)';
COMMENT ON COLUMN image_generations.provider IS 'Image generation provider (flux_pro, flux_dev, flux_schnell, dalle3, imagen3, sdxl_turbo)';
COMMENT ON COLUMN image_generations.generation_type IS 'Type of generation (product_shot, lifestyle, thumbnail, generic)';
COMMENT ON COLUMN image_generations.cost_estimate IS 'Estimated cost in USD for generation';
