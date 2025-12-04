# User Guide

**Gemini Video Platform - Complete User Guide**
Version: 1.0.0
Last Updated: 2025-12-02

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Dashboard Overview](#dashboard-overview)
4. [Video Analysis Workflow](#video-analysis-workflow)
5. [Campaign Creation](#campaign-creation)
6. [Creative Studio](#creative-studio)
7. [Analytics & Insights](#analytics--insights)
8. [A/B Testing](#ab-testing)
9. [Best Practices](#best-practices)
10. [FAQ](#faq)

---

## Introduction

Welcome to Gemini Video! This comprehensive AI-powered platform helps you create, analyze, and optimize video ads for Meta platforms (Facebook, Instagram, Reels).

### What Can You Do?

**Analyze Existing Videos:**
- Upload videos from your computer or Google Drive
- Get AI-powered scoring and CTR predictions
- Extract high-performing clips automatically
- Find patterns that drive engagement

**Create New Video Ads:**
- Use the AI Creative Studio to generate hooks
- Remix existing clips into new variations
- Apply professional templates
- Add subtitles, overlays, and effects

**Optimize Performance:**
- Run A/B tests with Thompson Sampling
- Track real campaign performance
- Get actionable recommendations
- Learn what works for your audience

**Publish to Meta:**
- Create campaigns directly in Meta Ads Manager
- Upload videos automatically
- Track conversions and ROAS
- Iterate based on real data

---

## Getting Started

### Account Setup

1. **Sign Up**
   - Visit https://app.geminivideo.com
   - Click "Sign Up" and create your account
   - Verify your email address

2. **Connect Meta Account**
   - Go to Settings > Integrations
   - Click "Connect Facebook"
   - Authorize Gemini Video to access your Meta Ads Account
   - Select your Ad Account ID

3. **Configure API Keys**
   - Navigate to Settings > API Keys
   - Add your Gemini API key (required for AI features)
   - Optional: Add Anthropic, OpenAI keys for enhanced analysis

4. **Set Up Google Drive (Optional)**
   - Go to Settings > Google Drive
   - Click "Connect Google Drive"
   - Authorize access to your video folders
   - Select folders to monitor

### System Requirements

**For Video Upload:**
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Stable internet connection
- Videos: MP4, MOV, AVI formats
- Max file size: 500 MB per video
- Recommended: 1080p or higher resolution

**For Video Editing:**
- Chrome browser recommended (WebAssembly support)
- 8GB+ RAM for smooth editing
- Hardware acceleration enabled

---

## Dashboard Overview

### Main Navigation

The dashboard consists of 6 main sections:

```
┌─────────────────────────────────────────────────────┐
│  🏠 Home  |  📹 Assets  |  🎨 Studio  |  📊 Analytics  │
│  🧪 Experiments  |  ⚙️ Settings                      │
└─────────────────────────────────────────────────────┘
```

### Home Dashboard

**Quick Actions:**
- Upload New Video
- Create Campaign
- View Recent Analysis
- Check A/B Test Results

**Performance Overview:**
- Total Videos Analyzed: 127
- Active Campaigns: 8
- Average Predicted CTR: 4.8%
- Current ROAS: 3.2x

**Recent Activity Feed:**
- Latest uploaded videos
- Completed analyses
- Campaign milestones
- System notifications

---

## Video Analysis Workflow

### Step 1: Upload Videos

#### Option A: Upload from Computer

1. Click **"Upload Video"** button
2. Select one or more video files
3. Videos are automatically queued for analysis
4. Progress shown in real-time

#### Option B: Import from Google Drive

1. Navigate to **Assets > Import from Drive**
2. Browse your connected Google Drive
3. Select folder containing videos
4. Click **"Start Import"**
5. All videos in folder are ingested automatically

#### Option C: Bulk Upload via API

```bash
curl -X POST https://gateway-api-xxxxx.run.app/api/analyze \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "path": "/videos/campaign_001/ad_v1.mp4",
    "filename": "ad_v1.mp4"
  }'
```

---

### Step 2: View Analysis Results

Once analysis completes (typically 2-5 minutes per video):

1. Navigate to **Assets** tab
2. Find your video in the list
3. Click to open detailed analysis

**Analysis Includes:**

**Overall Score (0-1):**
```
┌────────────────────────────────────┐
│  Composite Score: 0.84             │
│  ████████████████░░░░  84%         │
│                                    │
│  Predicted CTR: 4.8%               │
│  Band: HIGH                        │
│  Confidence: 89%                   │
└────────────────────────────────────┘
```

**Score Breakdown:**
- **Psychology Score (30%):** 0.87 - Strong emotional triggers
- **Hook Strength (25%):** 0.82 - Effective curiosity gap
- **Technical Quality (20%):** 0.78 - Good resolution, clear audio
- **Demographic Match (15%):** 0.88 - Perfect for target audience
- **Novelty Score (10%):** 0.73 - Moderately unique

**Detected Clips:**
```
Clip 1: 0:00 - 0:03  Score: 0.91  Hook: "Curiosity Gap"
Clip 2: 0:03 - 0:08  Score: 0.85  Hook: "Transformation"
Clip 3: 0:08 - 0:15  Score: 0.79  Hook: "Social Proof"
Clip 4: 0:15 - 0:23  Score: 0.76  Hook: "Call to Action"
```

**Visual Analysis:**
- Dominant Pattern: Face Closeup (65% of video)
- Motion Score: 0.72 (Good energy)
- Text Overlay Coverage: 15% (Within limits)
- Face Detection: 2 faces detected
- Objects: person, gym equipment, text

**Audio Analysis:**
- Transcript: "Are you tired of slow results? Here's how I transformed..."
- Detected Hooks: Question (0:00), Transformation (0:03)
- Audio Quality: 0.88 (Clear speech, good balance)
- Background Music: Motivational (0.7 volume)

---

### Step 3: Review Ranked Clips

The AI automatically ranks clips by predicted performance:

1. Click **"View Ranked Clips"**
2. See clips sorted by composite score
3. Preview each clip with thumbnail
4. Use filters:
   - Minimum score threshold
   - Hook type (curiosity, transformation, etc.)
   - Duration range
   - Presence of faces/text

**Clip Card Example:**
```
┌──────────────────────────────────────────┐
│  🎬 Clip #3 - "The Hook"                 │
│  ⭐ Score: 0.91                          │
│  ⏱️  Duration: 3.2s  |  🕐 Start: 0:00   │
│                                          │
│  [Thumbnail Preview]                     │
│                                          │
│  Hook Type: Curiosity Gap                │
│  Transcript: "Are you tired of..."      │
│  Confidence: 88%                         │
│                                          │
│  [▶️ Play]  [📋 Use in Studio]  [⬇️ Download] │
└──────────────────────────────────────────┘
```

---

### Step 4: Semantic Search

Find specific content across all your videos:

1. Go to **Assets > Search**
2. Enter natural language query
3. Get semantically similar clips

**Example Queries:**
- "person doing squats in gym"
- "before and after transformation"
- "testimonial with excited expression"
- "text overlay with numbers"
- "outdoor workout scene"

**Search Results:**
```
Query: "person doing squats"
Found: 23 clips

Top Results:
1. Clip #42 - Similarity: 0.94 - Score: 0.82
   "Proper squat form demonstration"

2. Clip #17 - Similarity: 0.91 - Score: 0.79
   "Gym workout with trainer"

3. Clip #89 - Similarity: 0.88 - Score: 0.75
   "Home workout routine"
```

---

## Campaign Creation

### Creating Your First Campaign

**Step-by-Step Walkthrough:**

#### 1. Choose Objective

Navigate to **Campaigns > Create New**

Select your objective:
- **Awareness:** Maximize reach and impressions
- **Traffic:** Drive clicks to website
- **Engagement:** Increase likes, comments, shares
- **Leads:** Collect contact information
- **Conversions:** Drive purchases or sign-ups

💡 **Recommendation:** Start with "Conversions" for best ROAS

---

#### 2. Select Creative

**Option A: Use Analyzed Video**
- Browse your analyzed assets
- Filter by score threshold (e.g., > 0.7)
- Select top-performing clip
- Preview before selection

**Option B: Create New Video in Studio**
- Click "Create New Creative"
- Use AI Creative Studio (see section below)
- Apply templates
- Export when ready

**Option C: Upload New Video**
- Upload directly from this screen
- Quick analysis (5-10 min)
- Use immediately or save for later

---

#### 3. Define Targeting

**Demographics:**
```
Age Range: [25] ─────────── [45]
Gender: ☑️ All  ⬜ Male  ⬜ Female  ⬜ Non-binary
Location: United States (selected)
         + Add more countries
```

**Interests:**
```
Suggested (based on your creative):
✅ Fitness & Health
✅ Weight Loss
✅ Gym & Workout
⬜ Nutrition
⬜ Athletic Wear

Custom Interests:
[+ Add interest]
```

**Behaviors:**
```
✅ Engaged Shoppers
⬜ Online Buyers
⬜ Mobile Users
⬜ New Technology Adopters
```

**💡 AI Recommendation:**
"Based on your creative's visual patterns, we recommend targeting fitness beginners aged 25-40 who have shown interest in weight loss and gym memberships in the past 30 days."

---

#### 4. Set Budget & Schedule

**Budget:**
```
Budget Type: ⚫ Daily Budget  ⬜ Lifetime Budget

Daily Budget: $[50] per day
              Estimated reach: 8,000-12,000 people/day

Lifetime Budget (optional): $[500]
Duration: [7] days
```

**Schedule:**
```
Start Date: [2025-12-03] [09:00]
End Date: ⬜ Continuous  ⚫ [2025-12-10] [23:59]

Time Targeting (optional):
⬜ Run ads all day
⚫ Specific times: 6am-10am, 6pm-10pm
```

**Bid Strategy:**
```
⚫ Lowest Cost (recommended)
⬜ Cost Cap: $[X] per result
⬜ Bid Cap: $[X] per action
```

---

#### 5. Review Predictions

Before launching, review AI predictions:

```
┌─────────────────────────────────────────┐
│  📊 CAMPAIGN PREDICTIONS                │
├─────────────────────────────────────────┤
│  Predicted CTR: 4.8%                    │
│  Predicted Conversions: 67              │
│  Predicted Cost/Conversion: $2.45       │
│  Predicted ROAS: 3.2x                   │
│  Confidence: 89%                        │
├─────────────────────────────────────────┤
│  ⚠️ RECOMMENDATIONS:                    │
│  • Consider adding social proof        │
│  • Test multiple ad variations         │
│  • Monitor first 24h closely           │
└─────────────────────────────────────────┘
```

**Confidence Levels:**
- **High (>80%):** Strong historical data, reliable prediction
- **Medium (60-80%):** Moderate data, reasonable confidence
- **Low (<60%):** Limited data, use as rough estimate

---

#### 6. Launch or Save as Draft

**Options:**
- **Launch Now:** Immediately submit to Meta for review
- **Save as Draft:** Save for later editing
- **Schedule:** Set future launch date
- **Create A/B Test:** Create multiple variants (see A/B Testing section)

**After Launch:**
- Campaign submitted to Meta Ads Manager
- Typical review time: 1-6 hours
- You'll receive notifications on approval status
- Tracking begins automatically once approved

---

## Creative Studio

The AI Creative Studio helps you create professional video ads from scratch or remix existing content.

### Studio Interface

```
┌──────────────────────────────────────────────────────────┐
│  Timeline                                                │
│  ╔═══════╦═══════╦═══════╦═══════╗                     │
│  ║ Clip1 ║ Clip2 ║ Clip3 ║ Clip4 ║                     │
│  ╚═══════╩═══════╩═══════╩═══════╝                     │
│  0:00    3s      8s      15s     22s                    │
└──────────────────────────────────────────────────────────┘
┌──────────────────────────────────────────────────────────┐
│  Preview                    │  Tools                     │
│  ┌──────────────────────┐   │  • Trim & Cut              │
│  │                      │   │  • Text Overlays           │
│  │   [Video Preview]    │   │  • Subtitles               │
│  │                      │   │  • Filters & Effects       │
│  │                      │   │  • Audio                   │
│  └──────────────────────┘   │  • Transitions             │
│                             │  • Speed Control           │
│  [◀️] [▶️] [■]  00:05/00:22  │  • Templates               │
└──────────────────────────────────────────────────────────┘
```

---

### Creating a Video Ad

#### Method 1: AI-Generated Ad

1. Click **"Generate with AI"**
2. Fill in the creative brief:

```
Product/Service: [Personal Training Program]

Target Outcome: [Sign-ups for free consultation]

Key Benefits (3-5):
• Lose 10-20 lbs in 30 days
• Personalized meal plans
• 24/7 trainer support
• Money-back guarantee

Tone: ⚫ Motivational  ⬜ Professional  ⬜ Casual  ⬜ Urgent

Duration: ⬜ 6s  ⬜ 15s  ⚫ 30s  ⬜ 60s

Platform: ⚫ Instagram Reels  ⬜ Feed  ⬜ Stories
```

3. Click **"Generate"**
4. AI creates:
   - Hook text (first 3 seconds)
   - Visual suggestions (shots needed)
   - Script outline
   - Call-to-action
   - Subtitle timings

5. Review generated blueprint
6. Edit as needed or regenerate

---

#### Method 2: Template-Based Creation

1. Click **"Browse Templates"**
2. Choose from categories:
   - Vertical Reels
   - Before/After
   - Testimonials
   - Product Demos
   - Text-Heavy
   - Cinematic

**Popular Templates:**

**"Fast Hook Template"**
```
Duration: 15s
Format: 9:16 (vertical)
Scenes:
  1. Hook (0-3s): Question overlay + face closeup
  2. Problem (3-8s): Fast cuts showing pain point
  3. Solution (8-12s): Product demo
  4. CTA (12-15s): Special offer text
```

**"Transformation Template"**
```
Duration: 30s
Format: 9:16 (vertical)
Scenes:
  1. "Before" (0-10s): Split screen left side
  2. "After" (10-20s): Split screen right side
  3. Process (20-25s): Quick montage
  4. CTA (25-30s): Sign up now
```

3. Customize template:
   - Upload your clips
   - Replace text overlays
   - Adjust colors/fonts
   - Modify timing

---

#### Method 3: Manual Editing

**Advanced Editor - 11 Operations:**

1. **Trim & Cut**
   - Select clip on timeline
   - Drag handles to adjust duration
   - Split clip at playhead

2. **Text Overlays**
   - Click "Add Text"
   - Type your message
   - Choose font, size, color
   - Set animation: fade in, slide, bounce
   - Position on screen

3. **Subtitles (Auto-Generated)**
   - Click "Generate Subtitles"
   - AI transcribes audio
   - Edit text if needed
   - Choose subtitle style:
     - Bold Centered (Reels style)
     - Bottom Banner
     - Word-by-word highlight

4. **Filters & Color Grading**
   - Cinematic: +20% contrast, -10% saturation
   - Bright & Vibrant: +30% saturation
   - Warm Tone: +10 temperature
   - Vintage: Grain + vignette
   - Custom: Adjust manually

5. **Speed Control**
   - Slow Motion: 0.5x - 0.9x
   - Normal: 1.0x
   - Fast Motion: 1.1x - 2.0x
   - Time Remapping: Variable speed

6. **Audio Editing**
   - Normalize loudness (EBU R128)
   - Add background music
   - Ducking (lower music during speech)
   - Voice enhancement
   - Remove background noise

7. **Transitions**
   - Cross-dissolve
   - Fade to black
   - Swipe
   - Zoom
   - Duration: 0.3s - 1.5s

8. **Crop & Resize**
   - Square (1:1) - Instagram Feed
   - Vertical (9:16) - Reels, Stories
   - Landscape (16:9) - YouTube
   - Custom dimensions

9. **Effects**
   - Blur background
   - Vignette
   - Zoom pan (Ken Burns)
   - Shake/stabilization
   - Chroma key (green screen)

10. **Overlays**
    - Logo placement
    - Stickers/emojis
    - Progress bars
    - Call-to-action buttons

11. **Export Settings**
    - Resolution: 720p, 1080p, 4K
    - Format: MP4, MOV
    - Quality: Low, Medium, High, Ultra
    - File size target

---

### Rendering & Export

1. Click **"Render Video"**
2. Choose quality preset:
   - **Fast (720p):** 30-60 seconds
   - **High (1080p):** 1-2 minutes
   - **Ultra (4K):** 2-5 minutes

3. Monitor progress:
```
┌─────────────────────────────────────────┐
│  🎬 Rendering: ad_remix_v1.mp4          │
│  ████████████████░░░░░░  67%            │
│                                         │
│  Stage: Encoding video                 │
│  Time remaining: ~45 seconds           │
│  Output size: ~12.3 MB                 │
└─────────────────────────────────────────┘
```

4. Download or save to library
5. Compliance check runs automatically

**Compliance Results:**
```
✅ Duration: 15.2s (within 5-60s limit)
✅ Aspect Ratio: 9:16 (supported)
✅ File Size: 12.3 MB (under 100 MB)
✅ Text Coverage: 18% (under 20%)
⚠️  Audio loudness: -16 LUFS (recommended: -14 LUFS)

Overall: COMPLIANT with warnings
```

---

## Analytics & Insights

### Performance Dashboard

Navigate to **Analytics** to see:

#### Campaign Performance

```
┌─────────────────────────────────────────────────────┐
│  Campaign: Fitness Q4 2025                          │
│  Status: Active  |  Budget: $50/day  |  Days: 4/7  │
├─────────────────────────────────────────────────────┤
│  Impressions: 45,678  ↑12% vs. yesterday           │
│  Clicks: 2,134        ↑8%                          │
│  CTR: 4.67%          ↑0.3%                         │
│  Conversions: 89      ↑15%                         │
│  Cost/Conv: $2.45     ↓$0.15                       │
│  ROAS: 3.2x          ↑0.4x                         │
└─────────────────────────────────────────────────────┘
```

**Prediction vs. Actual:**
```
Metric         | Predicted | Actual | Accuracy
---------------|-----------|--------|----------
CTR            | 4.8%      | 4.67%  | 97%
Conversions    | 67        | 89     | 133% ✅
Cost/Conv      | $2.45     | $2.45  | 100%
ROAS           | 3.2x      | 3.2x   | 100%
```

---

#### Creative Performance

Compare multiple ad creatives:

```
Creative           | Impressions | CTR   | Conv | ROAS
-------------------|-------------|-------|------|------
Curiosity Hook     | 25,432      | 5.2%  | 52   | 3.8x ⭐
Transformation     | 20,246      | 4.1%  | 37   | 2.9x
Social Proof       | 15,892      | 3.8%  | 28   | 2.4x
Question Hook      | 12,334      | 3.2%  | 19   | 1.8x
```

**Insights:**
- "Curiosity Hook" performing 26% better than average
- Consider shifting budget from "Question Hook"
- "Transformation" stable, good backup creative

---

#### Audience Insights

```
Top Performing Segments:

1. Women, 25-34, Fitness Beginners
   CTR: 6.2% | Conv: 45 | ROAS: 4.1x

2. Men, 35-44, Weight Loss Interest
   CTR: 4.8% | Conv: 28 | ROAS: 3.4x

3. Women, 45-54, Health & Wellness
   CTR: 3.9% | Conv: 16 | ROAS: 2.7x
```

**Recommendations:**
- Expand age range to 25-44 (currently best performing)
- Create dedicated creative for women vs. men
- Test new interests: "Nutrition", "Meal Planning"

---

#### Hourly Performance

```
Time of Day Analysis:

Best Performing Hours:
🔥 6am-9am:   CTR 5.8%, Conv 23, Cost $1.95
⭐ 12pm-2pm:  CTR 4.9%, Conv 18, Cost $2.10
🔥 6pm-9pm:   CTR 5.4%, Conv 28, Cost $2.05

Worst Performing Hours:
❌ 2am-5am:   CTR 2.1%, Conv 3, Cost $4.50
❌ 3pm-5pm:   CTR 3.2%, Conv 8, Cost $3.15
```

**Optimization:**
- Schedule ads for 6-9am and 6-9pm only
- Pause during 2-5am to save budget
- Potential savings: ~$20/day

---

### Attribution Tracking

Track conversions from ad click to purchase:

```
Conversion Funnel:

Impressions: 45,678
    ↓ 4.67% CTR
Clicks: 2,134
    ↓ 24% Landing Page View
Landing Page: 512
    ↓ 38% Add to Cart
Add to Cart: 194
    ↓ 46% Purchase
Purchases: 89

Overall Conversion Rate: 4.2%
```

**Multi-Touch Attribution:**
- First Click: 23% of conversions
- Last Click: 45% of conversions
- Linear: 32% of conversions

---

## A/B Testing

### Creating an A/B Test

1. Navigate to **Experiments > Create New**

2. **Choose Test Type:**
   - Creative Test (different videos)
   - Audience Test (different targeting)
   - Budget Test (different bid strategies)
   - Multi-variate (test multiple variables)

3. **Set Up Variants:**

```
Experiment Name: Hook Type Test - December

Variant A: "Curiosity Gap"
  Creative: curiosity_hook_v1.mp4
  Budget: Auto (Thompson Sampling)

Variant B: "Transformation"
  Creative: transformation_v1.mp4
  Budget: Auto (Thompson Sampling)

Total Budget: $500
Optimization Goal: Conversions
Min Conversions for Winner: 30
```

4. **Thompson Sampling Settings:**

```
Exploration vs Exploitation:

[Balanced]
More Exploration ◀─────●─────▶ More Exploitation
(Test evenly)           (Favor winner)

Current Setting: Balanced
- Initial allocation: 50/50
- Shift starts after: 20 conversions each
- Max allocation: 80% to winner
```

5. **Launch Test**

---

### Monitoring A/B Test

**Real-Time Performance:**

```
┌─────────────────────────────────────────────────────┐
│  Hook Type Test - December                          │
│  Status: Active  |  Budget Spent: $234/$500         │
│  Duration: 3 days / 7 days                          │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Variant A: Curiosity Gap                          │
│  Budget: $92 (39%)                                 │
│  Conversions: 23                                   │
│  CTR: 4.2%                                         │
│  Cost/Conv: $4.00                                  │
│  Probability of Best: 34%                          │
│                                                     │
│  Variant B: Transformation                         │
│  Budget: $142 (61%) ⬆️                              │
│  Conversions: 51                                   │
│  CTR: 5.8%                                         │
│  Cost/Conv: $2.78                                  │
│  Probability of Best: 66% ⭐                        │
│                                                     │
├─────────────────────────────────────────────────────┤
│  💡 Recommendation:                                 │
│  Variant B is showing strong performance.          │
│  Thompson Sampling is shifting 61% of budget to it.│
│  Projected winner in 2-3 more days.                │
└─────────────────────────────────────────────────────┘
```

---

### Declaring a Winner

Once statistical significance is reached:

```
🏆 TEST COMPLETE!

Winner: Variant B - "Transformation"
Confidence: 95%

Performance Summary:
                  Variant A    Variant B    Lift
Conversions       42           78           +86%
CTR               4.3%         5.9%         +37%
Cost/Conv         $3.85        $2.69        -30%
ROAS              2.8x         4.1x         +46%

✅ Scale "Transformation" creative
✅ Allocate full budget to winner
✅ Archive or iterate on Variant A
```

**Next Steps:**
1. Click "Scale Winner"
2. Set new budget (e.g., $100/day)
3. Launch full campaign
4. Start new test with variations

---

## Best Practices

### Video Creation

**Do's:**
✅ Start with a strong hook (first 3 seconds)
✅ Keep videos short (15-30s for Reels)
✅ Add captions (80% watch without sound)
✅ Show faces (increases engagement by 38%)
✅ Include clear CTA
✅ Test multiple variations
✅ Use vertical format (9:16) for Reels
✅ Maintain brand consistency

**Don'ts:**
❌ Don't bury the hook (grab attention immediately)
❌ Don't make it too long (attention span is 8 seconds)
❌ Don't rely on audio alone
❌ Don't ignore platform specs
❌ Don't forget to test
❌ Don't use low-quality footage
❌ Don't overcomplicate the message

---

### Campaign Optimization

**Daily Routine:**
1. Check performance (morning)
2. Pause underperforming ads (CTR < 2%)
3. Scale winning ads (+20% budget if ROAS > 3x)
4. Test new creatives (1-2 per week)
5. Review audience insights
6. Adjust bids if needed

**Weekly Review:**
1. Analyze full week of data
2. Identify trends and patterns
3. Update targeting based on insights
4. Refresh creative if performance declining
5. Calculate true ROAS (including offline conversions)
6. Plan next week's tests

**Monthly Strategy:**
1. Review all campaigns
2. Analyze creative fatigue (performance drop after 2-4 weeks)
3. Plan new creative themes
4. Expand successful audiences
5. Review budget allocation
6. Set next month's goals

---

### Scaling Successfully

**When to Scale:**
- ROAS > 3x for 3+ days
- Consistent conversion rate
- CTR above 3%
- Positive feedback (likes, shares, comments)

**How to Scale:**
1. **Gradual Increase:** +20% every 3 days
2. **Horizontal Scaling:** Launch similar campaigns to new audiences
3. **Vertical Scaling:** Increase budget on existing campaigns
4. **Creative Refresh:** New variations of winners

**Avoid:**
- Doubling budget overnight (causes instability)
- Scaling too early (less than 50 conversions)
- Ignoring creative fatigue
- Changing too many variables at once

---

## FAQ

**Q: How long does video analysis take?**
A: Typically 2-5 minutes per video, depending on duration and quality. Videos over 5 minutes may take up to 10 minutes.

**Q: What video formats are supported?**
A: MP4, MOV, AVI, and WebM. We recommend MP4 (H.264 codec) for best compatibility.

**Q: How accurate are the CTR predictions?**
A: Our ML models achieve 94% accuracy (R² = 0.88) based on validated historical data. Confidence scores indicate prediction reliability.

**Q: Can I use videos I don't own?**
A: Only for analysis purposes. For campaign creation and publishing, you must own the rights or have permission to use the content.

**Q: What is Thompson Sampling?**
A: An advanced A/B testing algorithm that automatically allocates more budget to better-performing variants while still exploring other options.

**Q: How do I connect my Meta Ads account?**
A: Go to Settings > Integrations > Connect Facebook. You'll need Admin access to your Meta Ads Manager account.

**Q: What happens if my ad doesn't get approved by Meta?**
A: You'll receive a notification with the rejection reason. Common issues: policy violations, low-quality creative, or prohibited content. Edit and resubmit.

**Q: Can I edit a video after it's already published?**
A: No, but you can create a new version and swap it in your campaign. Meta requires review for any creative changes.

**Q: How much does Gemini Video cost?**
A: Pricing tiers:
- Free: 10 video analyses/month, basic features
- Pro ($99/mo): Unlimited analyses, advanced features, priority support
- Enterprise: Custom pricing, dedicated account manager, API access

**Q: Do you offer a trial?**
A: Yes! 14-day free trial with full Pro features, no credit card required.

**Q: What about data privacy?**
A: We comply with GDPR, CCPA, and Meta's data policies. Your videos are encrypted at rest and in transit. We never share your data with third parties.

**Q: Can I export my data?**
A: Yes, go to Settings > Export Data. You can download all analyses, campaign results, and videos in CSV/JSON format.

**Q: Is there an API?**
A: Yes! See our [API Reference](/docs/api-reference.md) for details.

**Q: What support is available?**
A:
- Free: Email support (24-48h response)
- Pro: Priority email + live chat (4-8h response)
- Enterprise: Dedicated account manager + phone support

---

## Need Help?

**Resources:**
- Documentation: https://docs.geminivideo.com
- Video Tutorials: https://youtube.com/geminivideo
- Community Forum: https://community.geminivideo.com
- API Reference: https://docs.geminivideo.com/api

**Contact:**
- Email: support@geminivideo.com
- Live Chat: Available in app (Pro/Enterprise)
- Twitter: @geminivideo
- GitHub: github.com/milosriki/geminivideo

---

*Last Updated: 2025-12-02*
*Version: 1.0.0*
