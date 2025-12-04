-- ============================================
-- GEMINIVIDEO PRODUCTION DATABASE SCHEMA
-- Run this in Supabase Dashboard → SQL Editor
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USERS TABLE (extends Supabase auth.users)
-- ============================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    full_name TEXT,
    avatar_url TEXT,
    subscription_tier TEXT DEFAULT 'free',
    monthly_credits INT DEFAULT 100,
    credits_used INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- CAMPAIGNS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS public.campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    status TEXT DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'completed', 'archived')),
    target_audience JSONB DEFAULT '{}',
    budget DECIMAL(10, 2),
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    meta_campaign_id TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- BLUEPRINTS TABLE (Ad Scripts)
-- ============================================
CREATE TABLE IF NOT EXISTS public.blueprints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES public.campaigns(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    hook_type TEXT NOT NULL,
    hook_text TEXT,
    script TEXT NOT NULL,
    scenes JSONB DEFAULT '[]',
    council_score FLOAT,
    council_breakdown JSONB DEFAULT '{}',
    oracle_prediction JSONB DEFAULT '{}',
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'rendering', 'completed')),
    version INT DEFAULT 1,
    parent_id UUID REFERENCES public.blueprints(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- RENDER JOBS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS public.render_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    blueprint_id UUID REFERENCES public.blueprints(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'queued' CHECK (status IN ('queued', 'processing', 'rendering', 'completed', 'failed', 'cancelled')),
    progress INT DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),
    output_url TEXT,
    output_format TEXT DEFAULT 'mp4',
    resolution TEXT DEFAULT '1080x1920',
    duration_seconds FLOAT,
    file_size_bytes BIGINT,
    error_message TEXT,
    worker_id TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- VIDEOS TABLE (Uploaded/Generated)
-- ============================================
CREATE TABLE IF NOT EXISTS public.videos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES public.campaigns(id) ON DELETE SET NULL,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    render_job_id UUID REFERENCES public.render_jobs(id) ON DELETE SET NULL,
    storage_url TEXT NOT NULL,
    thumbnail_url TEXT,
    title TEXT,
    duration_seconds FLOAT,
    file_size_bytes BIGINT,
    format TEXT,
    resolution TEXT,
    analysis_data JSONB DEFAULT '{}',
    performance_data JSONB DEFAULT '{}',
    status TEXT DEFAULT 'ready' CHECK (status IN ('uploading', 'processing', 'ready', 'published', 'archived')),
    published_to JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- WINNING PATTERNS TABLE (Knowledge Base)
-- ============================================
CREATE TABLE IF NOT EXISTS public.winning_patterns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    pattern_type TEXT NOT NULL,
    pattern_name TEXT NOT NULL,
    description TEXT,
    example_videos JSONB DEFAULT '[]',
    performance_metrics JSONB DEFAULT '{}',
    hook_templates JSONB DEFAULT '[]',
    visual_elements JSONB DEFAULT '[]',
    audio_elements JSONB DEFAULT '[]',
    effectiveness_score FLOAT,
    usage_count INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- META PERFORMANCE TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS public.meta_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID REFERENCES public.campaigns(id) ON DELETE CASCADE,
    video_id UUID REFERENCES public.videos(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    impressions INT DEFAULT 0,
    clicks INT DEFAULT 0,
    conversions INT DEFAULT 0,
    spend DECIMAL(10, 2) DEFAULT 0,
    revenue DECIMAL(10, 2) DEFAULT 0,
    roas DECIMAL(5, 2) GENERATED ALWAYS AS (
        CASE WHEN spend > 0 THEN revenue / spend ELSE 0 END
    ) STORED,
    ctr DECIMAL(5, 4) GENERATED ALWAYS AS (
        CASE WHEN impressions > 0 THEN clicks::DECIMAL / impressions ELSE 0 END
    ) STORED,
    cvr DECIMAL(5, 4) GENERATED ALWAYS AS (
        CASE WHEN clicks > 0 THEN conversions::DECIMAL / clicks ELSE 0 END
    ) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- CHAT HISTORY TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS public.chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    video_id UUID REFERENCES public.videos(id) ON DELETE SET NULL,
    session_id UUID NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- INDEXES
-- ============================================
CREATE INDEX IF NOT EXISTS idx_campaigns_user_id ON public.campaigns(user_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_status ON public.campaigns(status);
CREATE INDEX IF NOT EXISTS idx_blueprints_campaign_id ON public.blueprints(campaign_id);
CREATE INDEX IF NOT EXISTS idx_blueprints_user_id ON public.blueprints(user_id);
CREATE INDEX IF NOT EXISTS idx_blueprints_status ON public.blueprints(status);
CREATE INDEX IF NOT EXISTS idx_render_jobs_blueprint_id ON public.render_jobs(blueprint_id);
CREATE INDEX IF NOT EXISTS idx_render_jobs_status ON public.render_jobs(status);
CREATE INDEX IF NOT EXISTS idx_videos_campaign_id ON public.videos(campaign_id);
CREATE INDEX IF NOT EXISTS idx_videos_user_id ON public.videos(user_id);
CREATE INDEX IF NOT EXISTS idx_meta_performance_date ON public.meta_performance(date);
CREATE INDEX IF NOT EXISTS idx_meta_performance_campaign_id ON public.meta_performance(campaign_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_user_id ON public.chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_history_session_id ON public.chat_history(session_id);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on all tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.campaigns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.blueprints ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.render_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.videos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.winning_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meta_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;

-- Profiles: Users can only see/edit their own profile
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

-- Campaigns: Users can only see/edit their own campaigns
CREATE POLICY "Users can view own campaigns" ON public.campaigns
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own campaigns" ON public.campaigns
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own campaigns" ON public.campaigns
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own campaigns" ON public.campaigns
    FOR DELETE USING (auth.uid() = user_id);

-- Blueprints: Users can only see/edit their own blueprints
CREATE POLICY "Users can view own blueprints" ON public.blueprints
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own blueprints" ON public.blueprints
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own blueprints" ON public.blueprints
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own blueprints" ON public.blueprints
    FOR DELETE USING (auth.uid() = user_id);

-- Render Jobs: Users can only see/edit their own jobs
CREATE POLICY "Users can view own render jobs" ON public.render_jobs
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own render jobs" ON public.render_jobs
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own render jobs" ON public.render_jobs
    FOR UPDATE USING (auth.uid() = user_id);

-- Videos: Users can only see/edit their own videos
CREATE POLICY "Users can view own videos" ON public.videos
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own videos" ON public.videos
    FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY "Users can update own videos" ON public.videos
    FOR UPDATE USING (auth.uid() = user_id);
CREATE POLICY "Users can delete own videos" ON public.videos
    FOR DELETE USING (auth.uid() = user_id);

-- Winning Patterns: Everyone can read (knowledge base is shared)
CREATE POLICY "Everyone can view winning patterns" ON public.winning_patterns
    FOR SELECT USING (true);

-- Meta Performance: Users can only see their own performance data
CREATE POLICY "Users can view own performance" ON public.meta_performance
    FOR SELECT USING (
        campaign_id IN (SELECT id FROM public.campaigns WHERE user_id = auth.uid())
    );

-- Chat History: Users can only see their own chat history
CREATE POLICY "Users can view own chat history" ON public.chat_history
    FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can create own chat history" ON public.chat_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================
-- FUNCTIONS
-- ============================================

-- Auto-update timestamps
CREATE OR REPLACE FUNCTION public.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
CREATE TRIGGER update_campaigns_updated_at BEFORE UPDATE ON public.campaigns
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
CREATE TRIGGER update_blueprints_updated_at BEFORE UPDATE ON public.blueprints
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
CREATE TRIGGER update_videos_updated_at BEFORE UPDATE ON public.videos
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();
CREATE TRIGGER update_winning_patterns_updated_at BEFORE UPDATE ON public.winning_patterns
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at();

-- Auto-create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================
-- SAMPLE WINNING PATTERNS DATA
-- ============================================
INSERT INTO public.winning_patterns (pattern_type, pattern_name, description, hook_templates, effectiveness_score) VALUES
('hook', 'Pattern Interrupt', 'Stops scroll with unexpected visual or statement',
 '["STOP scrolling if you {pain_point}", "This is exactly why {pain_point}"]', 92.5),
('hook', 'Curiosity Gap', 'Creates curiosity that must be satisfied',
 '["What if you could {desire} in just {timeframe}?", "The secret to {desire} that {authority} dont want you to know"]', 88.3),
('hook', 'Social Proof', 'Leverages testimonials and results',
 '["See how {person} achieved {result} in {timeframe}", "{number} people have already {result}"]', 85.7),
('transformation', 'Before/After', 'Shows dramatic transformation visually',
 '["From {before_state} to {after_state}", "Watch this transformation"]', 94.2),
('cta', 'Urgency', 'Creates time pressure',
 '["Only {number} spots left", "Offer ends {timeframe}"]', 79.8)
ON CONFLICT DO NOTHING;

-- ============================================
-- STORAGE BUCKETS (run in Supabase Dashboard → Storage)
-- ============================================
-- Note: Create these buckets manually in Supabase Dashboard:
-- 1. videos (public)
-- 2. thumbnails (public)
-- 3. assets (public)
-- 4. exports (private - authenticated users only)

SELECT 'Schema created successfully!' as status;
