-- ============================================================================
-- SEED DATA FOR TESTING
-- ============================================================================

-- Note: This seed file uses fixed UUIDs for easier testing and development
-- In production, these would be generated automatically

-- ============================================================================
-- USERS
-- ============================================================================

-- Insert test users
INSERT INTO users (id, email, full_name, avatar_url, created_at)
VALUES
    ('00000000-0000-0000-0000-000000000001', 'john@example.com', 'John Smith', 'https://i.pravatar.cc/150?img=1', '2024-01-01 10:00:00+00'),
    ('00000000-0000-0000-0000-000000000002', 'jane@example.com', 'Jane Doe', 'https://i.pravatar.cc/150?img=2', '2024-01-02 10:00:00+00'),
    ('00000000-0000-0000-0000-000000000003', 'mike@example.com', 'Mike Johnson', 'https://i.pravatar.cc/150?img=3', '2024-01-03 10:00:00+00')
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- CAMPAIGNS
-- ============================================================================

INSERT INTO campaigns (id, user_id, product_name, offer, target_avatar, pain_points, desires, status, total_generated, approved_count, rejected_count, created_at, updated_at)
VALUES
    (
        '10000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000001',
        'FitnessPro Resistance Bands',
        '50% OFF + Free Workout Guide',
        'Busy professionals (25-45) who want to stay fit at home',
        '["No time for gym", "Expensive gym memberships", "Limited space at home", "Inconsistent workout routine"]'::jsonb,
        '["Get fit at home", "Save time and money", "Build muscle and tone", "Feel confident and energetic"]'::jsonb,
        'completed',
        10,
        7,
        3,
        '2024-11-01 09:00:00+00',
        '2024-11-01 14:30:00+00'
    ),
    (
        '10000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000001',
        'SkinGlow Vitamin C Serum',
        'Buy 2 Get 1 Free + Free Shipping',
        'Women 30-50 concerned about aging and skin health',
        '["Dark spots and wrinkles", "Dull skin tone", "Sun damage", "Expensive dermatologist visits"]'::jsonb,
        '["Youthful glowing skin", "Fade dark spots", "Natural ingredients", "Look younger without surgery"]'::jsonb,
        'generating',
        5,
        3,
        0,
        '2024-11-15 11:00:00+00',
        '2024-11-15 11:30:00+00'
    ),
    (
        '10000000-0000-0000-0000-000000000003',
        '00000000-0000-0000-0000-000000000002',
        'MindMaster Productivity Course',
        '$100 OFF - Limited Time',
        'Entrepreneurs and professionals struggling with productivity',
        '["Constant distractions", "Procrastination", "Overwhelmed by tasks", "Poor time management"]'::jsonb,
        '["10x productivity", "Achieve goals faster", "Work-life balance", "Build successful habits"]'::jsonb,
        'draft',
        0,
        0,
        0,
        '2024-11-20 15:00:00+00',
        '2024-11-20 15:00:00+00'
    )
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- BLUEPRINTS
-- ============================================================================

INSERT INTO blueprints (id, campaign_id, title, hook_text, hook_type, script_json, council_score, predicted_roas, confidence, verdict, rank, created_at)
VALUES
    (
        '20000000-0000-0000-0000-000000000001',
        '10000000-0000-0000-0000-000000000001',
        'No Time For Gym? No Problem!',
        'I used to waste $100/month on a gym membership I never used...',
        'problem_agitate_solve',
        '{
            "hook": "I used to waste $100/month on a gym membership I never used...",
            "problem": "Between work, family, and everything else, who has time for the gym?",
            "agitate": "And even when you DO have time, you waste 30 minutes driving there and back.",
            "solution": "That is why I switched to FitnessPro Resistance Bands. Full body workout in 20 minutes, at home.",
            "proof": "I have been using them for 3 months and I am in the best shape of my life.",
            "cta": "Get 50% OFF plus a free workout guide. Link in bio!"
        }'::jsonb,
        94.5,
        5.8,
        89.0,
        'approved',
        1,
        '2024-11-01 09:30:00+00'
    ),
    (
        '20000000-0000-0000-0000-000000000002',
        '10000000-0000-0000-0000-000000000001',
        'This Changed My Fitness Game',
        'POV: You found the perfect home workout solution',
        'transformation',
        '{
            "hook": "POV: You found the perfect home workout solution",
            "before": "Before: Skipping workouts because gym is too far",
            "after": "After: Full body workout done before morning coffee",
            "secret": "The secret? FitnessPro Resistance Bands",
            "benefits": "Targets every muscle group, fits in your drawer, costs less than one month of gym",
            "cta": "50% OFF today only. Do not miss out!"
        }'::jsonb,
        91.2,
        4.9,
        85.5,
        'approved',
        2,
        '2024-11-01 09:45:00+00'
    ),
    (
        '20000000-0000-0000-0000-000000000003',
        '10000000-0000-0000-0000-000000000001',
        'Trainer Reveals Secret',
        'As a personal trainer, I recommend these to ALL my clients',
        'authority',
        '{
            "hook": "As a personal trainer, I recommend these to ALL my clients",
            "authority": "I have trained over 500 people in the last 5 years",
            "insight": "The biggest obstacle is not motivation, it is convenience",
            "recommendation": "That is why FitnessPro Resistance Bands are a game changer",
            "proof": "My clients see results in 2-3 weeks, guaranteed",
            "cta": "Try them risk-free with 50% OFF today"
        }'::jsonb,
        88.7,
        4.2,
        82.0,
        'approved',
        3,
        '2024-11-01 10:00:00+00'
    ),
    (
        '20000000-0000-0000-0000-000000000004',
        '10000000-0000-0000-0000-000000000001',
        'Weak Hook - Generic Message',
        'Check out these resistance bands!',
        'direct',
        '{
            "hook": "Check out these resistance bands!",
            "features": "They are really good quality and come in different colors",
            "price": "They are on sale right now",
            "cta": "Buy them today!"
        }'::jsonb,
        45.3,
        1.2,
        35.0,
        'rejected',
        NULL,
        '2024-11-01 10:15:00+00'
    ),
    (
        '20000000-0000-0000-0000-000000000005',
        '10000000-0000-0000-0000-000000000002',
        'Dermatologists Hate This Trick',
        'I spent $5000 on treatments before discovering this $29 serum...',
        'secret_reveal',
        '{
            "hook": "I spent $5000 on treatments before discovering this $29 serum...",
            "struggle": "Dark spots, wrinkles, dull skin - I tried everything",
            "discovery": "Then my friend who is a dermatologist told me about Vitamin C",
            "solution": "SkinGlow Vitamin C Serum changed everything in 4 weeks",
            "proof": "My skin is glowing, dark spots fading, wrinkles softening",
            "cta": "Buy 2 Get 1 Free + Free Shipping. Your skin will thank you!"
        }'::jsonb,
        92.8,
        6.2,
        88.5,
        'approved',
        1,
        '2024-11-15 11:10:00+00'
    ),
    (
        '20000000-0000-0000-0000-000000000006',
        '10000000-0000-0000-0000-000000000002',
        '30 Days Skin Transformation',
        'Day 1 vs Day 30 using SkinGlow Vitamin C Serum',
        'before_after',
        '{
            "hook": "Day 1 vs Day 30 using SkinGlow Vitamin C Serum",
            "before": "Tired, dull skin with dark spots",
            "after": "Radiant, glowing, youthful skin",
            "how": "Just 2 drops morning and night",
            "ingredients": "Pure Vitamin C + Hyaluronic Acid + Vitamin E",
            "cta": "Buy 2 Get 1 Free - Stock up and save!"
        }'::jsonb,
        89.5,
        5.5,
        84.0,
        'approved',
        2,
        '2024-11-15 11:15:00+00'
    )
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- RENDER JOBS
-- ============================================================================

INSERT INTO render_jobs (id, blueprint_id, campaign_id, platform, quality, status, progress, current_stage, error, started_at, completed_at, created_at)
VALUES
    (
        '30000000-0000-0000-0000-000000000001',
        '20000000-0000-0000-0000-000000000001',
        '10000000-0000-0000-0000-000000000001',
        'tiktok',
        'high',
        'completed',
        100,
        'upload_complete',
        NULL,
        '2024-11-01 12:00:00+00',
        '2024-11-01 12:15:00+00',
        '2024-11-01 11:55:00+00'
    ),
    (
        '30000000-0000-0000-0000-000000000002',
        '20000000-0000-0000-0000-000000000001',
        '10000000-0000-0000-0000-000000000001',
        'instagram',
        'high',
        'completed',
        100,
        'upload_complete',
        NULL,
        '2024-11-01 12:20:00+00',
        '2024-11-01 12:35:00+00',
        '2024-11-01 12:15:00+00'
    ),
    (
        '30000000-0000-0000-0000-000000000003',
        '20000000-0000-0000-0000-000000000002',
        '10000000-0000-0000-0000-000000000001',
        'youtube',
        'ultra',
        'completed',
        100,
        'upload_complete',
        NULL,
        '2024-11-01 13:00:00+00',
        '2024-11-01 13:25:00+00',
        '2024-11-01 12:55:00+00'
    ),
    (
        '30000000-0000-0000-0000-000000000004',
        '20000000-0000-0000-0000-000000000005',
        '10000000-0000-0000-0000-000000000002',
        'tiktok',
        'high',
        'processing',
        65,
        'video_composition',
        NULL,
        '2024-11-15 11:30:00+00',
        NULL,
        '2024-11-15 11:25:00+00'
    ),
    (
        '30000000-0000-0000-0000-000000000005',
        '20000000-0000-0000-0000-000000000003',
        '10000000-0000-0000-0000-000000000001',
        'facebook',
        'medium',
        'failed',
        45,
        'audio_processing',
        'Audio file corrupted during processing',
        '2024-11-01 14:00:00+00',
        '2024-11-01 14:10:00+00',
        '2024-11-01 13:55:00+00'
    )
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- VIDEOS
-- ============================================================================

INSERT INTO videos (id, campaign_id, blueprint_id, render_job_id, storage_path, storage_url, duration_seconds, resolution, file_size_bytes, platform, actual_roas, impressions, clicks, conversions, created_at)
VALUES
    (
        '40000000-0000-0000-0000-000000000001',
        '10000000-0000-0000-0000-000000000001',
        '20000000-0000-0000-0000-000000000001',
        '30000000-0000-0000-0000-000000000001',
        '00000000-0000-0000-0000-000000000001/campaigns/10000000-0000-0000-0000-000000000001/video_001.mp4',
        'https://storage.supabase.co/videos/00000000-0000-0000-0000-000000000001/campaigns/10000000-0000-0000-0000-000000000001/video_001.mp4',
        45.5,
        '1080x1920',
        15728640,
        'tiktok',
        8.5,
        125000,
        8500,
        425,
        '2024-11-01 12:15:00+00'
    ),
    (
        '40000000-0000-0000-0000-000000000002',
        '10000000-0000-0000-0000-000000000001',
        '20000000-0000-0000-0000-000000000001',
        '30000000-0000-0000-0000-000000000002',
        '00000000-0000-0000-0000-000000000001/campaigns/10000000-0000-0000-0000-000000000001/video_002.mp4',
        'https://storage.supabase.co/videos/00000000-0000-0000-0000-000000000001/campaigns/10000000-0000-0000-0000-000000000001/video_002.mp4',
        47.2,
        '1080x1920',
        16777216,
        'instagram',
        6.8,
        98000,
        6200,
        310,
        '2024-11-01 12:35:00+00'
    ),
    (
        '40000000-0000-0000-0000-000000000003',
        '10000000-0000-0000-0000-000000000001',
        '20000000-0000-0000-0000-000000000002',
        '30000000-0000-0000-0000-000000000003',
        '00000000-0000-0000-0000-000000000001/campaigns/10000000-0000-0000-0000-000000000001/video_003.mp4',
        'https://storage.supabase.co/videos/00000000-0000-0000-0000-000000000001/campaigns/10000000-0000-0000-0000-000000000001/video_003.mp4',
        60.0,
        '1920x1080',
        52428800,
        'youtube',
        5.2,
        45000,
        2800,
        140,
        '2024-11-01 13:25:00+00'
    ),
    (
        '40000000-0000-0000-0000-000000000004',
        '10000000-0000-0000-0000-000000000001',
        '20000000-0000-0000-0000-000000000002',
        NULL,
        '00000000-0000-0000-0000-000000000001/campaigns/10000000-0000-0000-0000-000000000001/video_004.mp4',
        'https://storage.supabase.co/videos/00000000-0000-0000-0000-000000000001/campaigns/10000000-0000-0000-0000-000000000001/video_004.mp4',
        46.8,
        '1080x1920',
        15200000,
        'tiktok',
        7.9,
        142000,
        9500,
        475,
        '2024-11-02 10:00:00+00'
    ),
    (
        '40000000-0000-0000-0000-000000000005',
        '10000000-0000-0000-0000-000000000001',
        '20000000-0000-0000-0000-000000000003',
        NULL,
        '00000000-0000-0000-0000-000000000001/campaigns/10000000-0000-0000-0000-000000000001/video_005.mp4',
        'https://storage.supabase.co/videos/00000000-0000-0000-0000-000000000001/campaigns/10000000-0000-0000-0000-000000000001/video_005.mp4',
        42.0,
        '1080x1920',
        14500000,
        'instagram',
        4.3,
        68000,
        3800,
        190,
        '2024-11-03 14:30:00+00'
    )
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- VERIFY DATA INTEGRITY
-- ============================================================================

-- Check that campaign counters are correct
DO $$
DECLARE
    campaign_record RECORD;
    expected_total INTEGER;
    expected_approved INTEGER;
    expected_rejected INTEGER;
BEGIN
    FOR campaign_record IN SELECT * FROM campaigns LOOP
        SELECT COUNT(*) INTO expected_total
        FROM blueprints
        WHERE campaign_id = campaign_record.id;

        SELECT COUNT(*) INTO expected_approved
        FROM blueprints
        WHERE campaign_id = campaign_record.id AND verdict = 'approved';

        SELECT COUNT(*) INTO expected_rejected
        FROM blueprints
        WHERE campaign_id = campaign_record.id AND verdict = 'rejected';

        -- Update if counters don't match
        IF campaign_record.total_generated != expected_total OR
           campaign_record.approved_count != expected_approved OR
           campaign_record.rejected_count != expected_rejected THEN
            UPDATE campaigns
            SET total_generated = expected_total,
                approved_count = expected_approved,
                rejected_count = expected_rejected
            WHERE id = campaign_record.id;

            RAISE NOTICE 'Updated counters for campaign %', campaign_record.id;
        END IF;
    END LOOP;
END $$;

-- Display summary
DO $$
DECLARE
    user_count INTEGER;
    campaign_count INTEGER;
    blueprint_count INTEGER;
    render_job_count INTEGER;
    video_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO user_count FROM users;
    SELECT COUNT(*) INTO campaign_count FROM campaigns;
    SELECT COUNT(*) INTO blueprint_count FROM blueprints;
    SELECT COUNT(*) INTO render_job_count FROM render_jobs;
    SELECT COUNT(*) INTO video_count FROM videos;

    RAISE NOTICE '===============================================';
    RAISE NOTICE 'SEED DATA SUMMARY';
    RAISE NOTICE '===============================================';
    RAISE NOTICE 'Users: %', user_count;
    RAISE NOTICE 'Campaigns: %', campaign_count;
    RAISE NOTICE 'Blueprints: %', blueprint_count;
    RAISE NOTICE 'Render Jobs: %', render_job_count;
    RAISE NOTICE 'Videos: %', video_count;
    RAISE NOTICE '===============================================';
END $$;
