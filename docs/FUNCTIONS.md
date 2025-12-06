# GeminiVideo Function Reference

Complete reference for all public functions in the AI ad platform.

---

## Video Analysis Functions

### motion_moment_sdk.py

#### `MotionMomentSDK.__init__(fps: float = 30.0)`
Initialize the Motion Moment SDK.

**Parameters:**
- `fps` (float): Video frame rate. Default: 30.0

**Constants:**
- `WINDOW_SIZE = 30` - 1 second at 30fps
- `FACE_WEIGHT = 3.2` - Faces get 3.2x priority

---

#### `MotionMomentSDK.calculate_motion_energy(frame1: np.ndarray, frame2: np.ndarray) -> float`
Calculate motion energy between two frames using Farneback optical flow.

**Parameters:**
- `frame1` (np.ndarray): First BGR frame
- `frame2` (np.ndarray): Second BGR frame

**Returns:** `float` - Mean motion magnitude

**Example:**
```python
sdk = MotionMomentSDK()
energy = sdk.calculate_motion_energy(frame1, frame2)
print(f"Motion energy: {energy}")  # e.g., 12.5
```

---

#### `MotionMomentSDK.analyze_temporal_window(frames: List[np.ndarray], face_detections: List[bool]) -> TemporalWindow`
Analyze a 30-frame window for motion patterns with 3.2x face weighting.

**Parameters:**
- `frames` (List[np.ndarray]): List of 30 video frames
- `face_detections` (List[bool]): Whether each frame has faces

**Returns:** `TemporalWindow` with:
- `frames`: Original frames
- `motion_energies`: Energy per frame pair
- `face_detections`: Face presence
- `weighted_energy`: Average weighted energy
- `peak_index`: Index of highest energy

---

#### `MotionMomentSDK.detect_motion_moments(video_path: str) -> List[MotionMoment]`
Detect all significant motion moments in a video.

**Parameters:**
- `video_path` (str): Path to video file

**Returns:** `List[MotionMoment]` with:
- `frame_start`, `frame_end`: Frame range
- `timestamp_start`, `timestamp_end`: Time range
- `motion_energy`: Energy level
- `peak_frame`, `peak_energy`: Peak details
- `moment_type`: 'hook', 'transition', 'emotional', 'action'
- `face_present`, `face_weight`: Face detection info

**Example:**
```python
sdk = MotionMomentSDK()
moments = sdk.detect_motion_moments("ad.mp4")
for m in moments:
    print(f"{m.moment_type} at {m.timestamp_start:.2f}s - energy: {m.motion_energy}")
```

---

#### `MotionMomentSDK.find_optimal_cut_points(moments: List[MotionMoment]) -> List[float]`
Find optimal timestamps for video cuts based on motion analysis.

**Parameters:**
- `moments` (List[MotionMoment]): Detected motion moments

**Returns:** `List[float]` - Sorted list of optimal cut timestamps

---

#### `MotionMomentSDK.get_attention_curve(video_path: str) -> Dict[str, List[float]]`
Generate attention prediction curve for a video.

**Parameters:**
- `video_path` (str): Path to video file

**Returns:** `Dict` with:
- `timeline`: Time points (0 to duration)
- `attention`: Predicted attention levels
- `moments`: List of motion moments

---

### precision_av_sync.py

#### `PrecisionAVSync.__init__(sr: int = 22050)`
Initialize precision audio-visual sync analyzer.

**Parameters:**
- `sr` (int): Audio sample rate. Default: 22050

**Constants:**
- `TOLERANCE = 0.1` - 100ms sync tolerance

---

#### `PrecisionAVSync.extract_audio_peaks(audio_path: str) -> List[AudioPeak]`
Extract all audio peaks including beats, onsets, and drops.

**Parameters:**
- `audio_path` (str): Path to audio file

**Returns:** `List[AudioPeak]` with:
- `timestamp`: Peak time in seconds
- `energy`: Normalized energy (0-1)
- `peak_type`: 'beat', 'onset', 'vocal', 'drop'

---

#### `PrecisionAVSync.extract_visual_peaks(video_path: str) -> List[VisualPeak]`
Extract all visual peaks including cuts, motion spikes, and transitions.

**Parameters:**
- `video_path` (str): Path to video file

**Returns:** `List[VisualPeak]` with:
- `timestamp`: Peak time in seconds
- `motion_energy`: Motion magnitude
- `peak_type`: 'cut', 'motion', 'face_appear', 'transition'

---

#### `PrecisionAVSync.find_sync_points(audio_peaks: List[AudioPeak], visual_peaks: List[VisualPeak]) -> List[SyncPoint]`
Match audio and visual peaks within 0.1s tolerance.

**Parameters:**
- `audio_peaks` (List[AudioPeak]): Audio peaks
- `visual_peaks` (List[VisualPeak]): Visual peaks

**Returns:** `List[SyncPoint]` with:
- `audio_peak`: Matched audio peak
- `visual_peak`: Matched visual peak
- `offset`: Time difference in seconds
- `is_synced`: True if within 0.1s tolerance
- `sync_score`: Quality score (0-1)

---

#### `PrecisionAVSync.analyze_sync_quality(video_path: str, audio_path: str = None) -> Dict`
Comprehensive audio-visual sync analysis.

**Parameters:**
- `video_path` (str): Path to video file
- `audio_path` (str, optional): Path to audio file (extracts from video if None)

**Returns:** `Dict` with:
- `total_audio_peaks`: Count of audio peaks
- `total_visual_peaks`: Count of visual peaks
- `sync_points_found`: Matched pairs
- `synced_within_tolerance`: Pairs within 0.1s
- `sync_percentage`: Percentage synced
- `average_offset_seconds`: Mean offset
- `average_sync_score`: Mean quality
- `recommendation`: Human-readable advice

**Example:**
```python
sync = PrecisionAVSync()
result = sync.analyze_sync_quality("ad.mp4")
print(f"Sync quality: {result['sync_percentage']:.1f}%")
print(f"Recommendation: {result['recommendation']}")
```

---

#### `PrecisionAVSync.suggest_cut_adjustments(sync_points: List[SyncPoint]) -> List[Dict]`
Suggest timing adjustments to improve sync.

**Parameters:**
- `sync_points` (List[SyncPoint]): Analyzed sync points

**Returns:** `List[Dict]` with:
- `current_visual_time`: Current cut time
- `target_audio_time`: Optimal cut time
- `adjustment_needed`: Seconds to adjust
- `direction`: 'earlier' or 'later'
- `priority`: 'high' or 'medium'

---

## ML Service Functions

### variation_generator.py

#### `VariationGenerator.__init__()`
Initialize variation generator with templates.

**Constants:**
- `TARGET_VARIATIONS = 50` - Generate 50 variations per concept

---

#### `VariationGenerator.generate_variations(concept: CreativeConcept, count: int = 50) -> List[CreativeVariation]`
Generate variations from a creative concept using 6 strategies.

**Parameters:**
- `concept` (CreativeConcept): Base creative concept
- `count` (int): Number of variations. Default: 50

**Returns:** `List[CreativeVariation]` with:
- `id`: Variation ID
- `concept_id`: Parent concept ID
- `variation_number`: 1-50
- `variations_applied`: Dict of changes
- `hook`, `headline`, `cta`: Content
- `color_scheme`: Color list
- `pacing`: 'fast', 'medium', 'slow'
- `duration`: 15, 30, or 60 seconds
- `predicted_performance`: ML score (0-1)

**Strategies:**
1. 10 hook variations
2. 10 CTA variations
3. 10 headline variations
4. 5 color variations
5. 9 pacing/duration combinations
6. 27 cross-combinations

**Example:**
```python
generator = VariationGenerator()
concept = CreativeConcept(
    id="c1",
    name="Product Launch",
    product="SuperWidget",
    key_benefit="saves time",
    pain_point="wasting hours",
    # ... other fields
)
variations = generator.generate_variations(concept, count=50)
print(f"Generated {len(variations)} variations")
```

---

#### `VariationGenerator.rank_variations(variations: List[CreativeVariation]) -> List[CreativeVariation]`
Rank variations by predicted performance.

**Parameters:**
- `variations` (List[CreativeVariation]): Variations to rank

**Returns:** `List[CreativeVariation]` - Sorted by performance (best first)

---

#### `VariationGenerator.get_top_variations(variations: List[CreativeVariation], count: int = 10) -> List[CreativeVariation]`
Get top N variations for rendering.

**Parameters:**
- `variations` (List[CreativeVariation]): All variations
- `count` (int): How many to return. Default: 10

**Returns:** `List[CreativeVariation]` - Top performers

---

#### `VariationGenerator.export_variations(variations: List[CreativeVariation]) -> List[Dict]`
Export variations for video rendering pipeline.

**Parameters:**
- `variations` (List[CreativeVariation]): Variations to export

**Returns:** `List[Dict]` with render-ready data including `render_priority`

---

### loser_kill_switch.py

#### `LoserKillSwitch.__init__(target_cpa: float = 50.0, target_roas: float = 2.0)`
Initialize kill switch with targets.

**Parameters:**
- `target_cpa` (float): Target cost per acquisition. Default: $50
- `target_roas` (float): Target return on ad spend. Default: 2.0x

**Thresholds:**
- `MIN_CTR = 0.005` (0.5%) after 1000 impressions
- `MIN_CVR = 0.005` (0.5%) after 100 clicks
- `MAX_CPA_MULTIPLIER = 3.0` - Kill if CPA > 3x target
- `MIN_ROAS = 0.5` - Kill if ROAS below 0.5x
- `NO_CONVERSION_SPEND_LIMIT = 100` - Kill after $100 with 0 conversions

---

#### `LoserKillSwitch.evaluate_ad(metrics: AdMetrics) -> KillDecision`
Evaluate an ad and decide whether to kill it.

**Parameters:**
- `metrics` (AdMetrics): Current ad performance metrics

**Returns:** `KillDecision` with:
- `ad_id`: Ad identifier
- `should_kill`: True/False
- `reason`: KillReason enum
- `confidence`: 0-1 confidence
- `waste_prevented`: $ saved
- `recommendation`: Human-readable advice
- `metrics_at_kill`: Metrics that triggered kill

**Kill Triggers:**
1. CTR < 0.5% after 1000 impressions
2. CVR < 0.5% after 100 clicks
3. CPA > 3x target after 3 conversions
4. ROAS < 0.5 after $100 spend
5. Zero conversions after $100 spend

**Example:**
```python
kill_switch = LoserKillSwitch(target_cpa=30.0)
metrics = AdMetrics(
    ad_id="ad_123",
    spend=120.0,
    conversions=0,
    # ... other metrics
)
decision = kill_switch.evaluate_ad(metrics)
if decision.should_kill:
    print(f"KILL: {decision.reason.value}")
    print(f"Waste prevented: ${decision.waste_prevented}")
```

---

#### `LoserKillSwitch.batch_evaluate(ads: List[AdMetrics]) -> List[KillDecision]`
Evaluate multiple ads at once.

**Parameters:**
- `ads` (List[AdMetrics]): List of ad metrics

**Returns:** `List[KillDecision]` - Only ads that should be killed, sorted by waste prevented

---

#### `LoserKillSwitch.execute_kill(decision: KillDecision, platform_client: Any = None) -> Dict`
Execute the kill by pausing the ad via platform API.

**Parameters:**
- `decision` (KillDecision): Kill decision to execute
- `platform_client` (Any): Platform API client (Meta, Google, etc.)

**Returns:** `Dict` with execution status

---

#### `LoserKillSwitch.get_kill_report(decisions: List[KillDecision]) -> Dict`
Generate summary report of kill decisions.

**Parameters:**
- `decisions` (List[KillDecision]): List of decisions

**Returns:** `Dict` with:
- `total_ads_to_kill`: Count
- `total_waste_prevented`: $ total
- `kill_reasons`: Breakdown by reason
- `highest_waste_ad`: Worst performer
- `average_confidence`: Mean confidence

---

### budget_optimizer.py

#### `BudgetOptimizer.__init__()`
Initialize budget optimizer.

**Thresholds:**
- `MIN_SPEND_FOR_DECISION = 50` - Need $50 spend before optimizing
- `TARGET_ROAS = 2.0` - Target return on ad spend
- `SCALE_ROAS_THRESHOLD = 3.0` - Scale up if ROAS >= 3.0

---

#### `BudgetOptimizer.generate_recommendations(ads: List[Dict]) -> List[BudgetRecommendation]`
Generate budget shift recommendations.

**Parameters:**
- `ads` (List[Dict]): Ads with performance data

**Returns:** `List[BudgetRecommendation]` with:
- `ad_id`: Ad identifier
- `current_budget`: Current daily budget
- `recommended_budget`: Suggested budget
- `change_percent`: Percentage change
- `reason`: Why the change
- `confidence`: 0-1 confidence

**Budget Rules:**
- ROAS >= 3.0: Increase up to +50%
- ROAS 2.0-3.0: Maintain budget
- ROAS 1.0-2.0: Decrease by 30%
- ROAS < 1.0: Decrease by 70%

---

### cross_campaign_learning.py

#### `CrossCampaignLearner.__init__()`
Initialize cross-campaign learning system.

---

#### `CrossCampaignLearner.learn_from_campaign(campaign_id: str, metrics: Dict) -> None`
Extract learnings from a completed campaign.

**Parameters:**
- `campaign_id` (str): Campaign identifier
- `metrics` (Dict): Campaign performance metrics

---

#### `CrossCampaignLearner.get_insights_for_industry(industry: str) -> Dict`
Get accumulated insights for an industry.

**Parameters:**
- `industry` (str): Industry name

**Returns:** `Dict` with:
- `avg_ctr`: Average CTR for industry
- `avg_roas`: Average ROAS
- `best_hooks`: Top performing hooks
- `best_ctas`: Top performing CTAs
- `best_colors`: Top color schemes

---

### capi_feedback_loop.py

#### `CAPIFeedbackLoop.__init__()`
Initialize CAPI feedback integration.

---

#### `CAPIFeedbackLoop.process_conversion(event: Dict) -> None`
Process incoming CAPI conversion event.

**Parameters:**
- `event` (Dict): Conversion event from Meta CAPI

---

#### `CAPIFeedbackLoop.get_training_data(since: datetime) -> List[Dict]`
Get conversion data for model training.

**Parameters:**
- `since` (datetime): Start date for data

**Returns:** `List[Dict]` - Conversion events with features

---

### auto_retrain_pipeline.py

#### `AutoRetrainPipeline.__init__()`
Initialize auto-retraining pipeline.

---

#### `AutoRetrainPipeline.check_drift() -> bool`
Check if model performance has drifted.

**Returns:** `bool` - True if retraining needed

---

#### `AutoRetrainPipeline.retrain() -> Dict`
Retrain the ML model with new data.

**Returns:** `Dict` with:
- `new_accuracy`: Updated accuracy
- `improvement`: Accuracy change
- `samples_used`: Training samples

---

### prediction_accuracy_tracker.py

#### `PredictionAccuracyTracker.__init__()`
Initialize accuracy tracking.

---

#### `PredictionAccuracyTracker.log_prediction(prediction_id: str, predicted: float) -> None`
Log a new prediction.

**Parameters:**
- `prediction_id` (str): Prediction identifier
- `predicted` (float): Predicted value

---

#### `PredictionAccuracyTracker.log_actual(prediction_id: str, actual: float) -> None`
Log actual outcome for a prediction.

**Parameters:**
- `prediction_id` (str): Prediction identifier
- `actual` (float): Actual value

---

#### `PredictionAccuracyTracker.get_accuracy_report() -> Dict`
Get accuracy metrics over time.

**Returns:** `Dict` with:
- `mape`: Mean absolute percentage error
- `accuracy_7d`: 7-day accuracy
- `accuracy_30d`: 30-day accuracy
- `drift_detected`: Whether drift is detected

---

## AI Generation Functions

### runway_gen3.py

#### `RunwayGen3Client.__init__(api_key: str)`
Initialize Runway Gen-3 client.

**Parameters:**
- `api_key` (str): Runway API key

---

#### `RunwayGen3Client.generate_video(prompt: str, duration: int = 5) -> str`
Generate AI video from text prompt.

**Parameters:**
- `prompt` (str): Text description
- `duration` (int): Video length (5 or 10 seconds)

**Returns:** `str` - URL to generated video

---

#### `RunwayGen3Client.generate_product_shot(product_image: str, scene: str) -> str`
Generate product video from image.

**Parameters:**
- `product_image` (str): Path to product image
- `scene` (str): Scene description

**Returns:** `str` - URL to generated video

---

### elevenlabs_voice.py

#### `ElevenLabsClient.__init__(api_key: str)`
Initialize ElevenLabs client.

**Parameters:**
- `api_key` (str): ElevenLabs API key

---

#### `ElevenLabsClient.generate_voiceover(text: str, voice: str = "adam") -> bytes`
Generate voiceover audio.

**Parameters:**
- `text` (str): Script text
- `voice` (str): Voice preset

**Returns:** `bytes` - Audio data

**Voice Presets:**
- adam, rachel, domi, josh, bella, antoni, elli, sam

---

#### `ElevenLabsClient.clone_voice(name: str, audio_samples: List[str]) -> str`
Clone a voice from audio samples.

**Parameters:**
- `name` (str): Voice name
- `audio_samples` (List[str]): Paths to audio files

**Returns:** `str` - Voice ID for future use

---

## Orchestrator Functions

### winning_ads_orchestrator.py

#### `WinningAdsOrchestrator.__init__()`
Initialize the main orchestrator.

---

#### `WinningAdsOrchestrator.process_request(request: CreativeRequest) -> OrchestratorResult`
Process a complete creative request through all 11 AI subsystems.

**Parameters:**
- `request` (CreativeRequest): Creative request with:
  - `concept`: Base concept
  - `target_audience`: Audience definition
  - `platform`: Meta, Google, TikTok
  - `budget`: Daily budget

**Returns:** `OrchestratorResult` with:
- `variations`: List of 50 variations
- `top_10`: Best 10 for rendering
- `predictions`: Performance predictions
- `ready_to_publish`: Rendered ads

**Flow:**
1. Cross-campaign learning lookup
2. Generate 50 variations
3. Predict performance with ML
4. Render top 10
5. Publish to platforms
6. Setup CAPI tracking

**Example:**
```python
orchestrator = WinningAdsOrchestrator()
result = await orchestrator.process_request(CreativeRequest(
    concept=my_concept,
    target_audience="women 25-45",
    platform="meta",
    budget=100
))
print(f"Published {len(result.ready_to_publish)} ads")
```

---

#### `WinningAdsOrchestrator.monitor_performance(campaign_id: str) -> Dict`
Monitor live campaign performance.

**Parameters:**
- `campaign_id` (str): Campaign to monitor

**Returns:** `Dict` with:
- `live_ads`: Active ads count
- `total_spend`: Spend so far
- `total_revenue`: Revenue generated
- `roas`: Current ROAS
- `kills_today`: Ads killed today
- `budget_shifts`: Budget optimizations made

---

## Data Classes

### MotionMoment
```python
@dataclass
class MotionMoment:
    frame_start: int
    frame_end: int
    timestamp_start: float
    timestamp_end: float
    motion_energy: float
    peak_frame: int
    peak_energy: float
    moment_type: str  # 'hook', 'transition', 'cta', 'emotional'
    face_present: bool
    face_weight: float  # 3.2x if face present
```

### CreativeConcept
```python
@dataclass
class CreativeConcept:
    id: str
    name: str
    description: str
    target_audience: str
    industry: str
    objective: str  # conversions, awareness, traffic
    product: str
    key_benefit: str
    pain_point: str
    social_proof: str
    brand_colors: List[str]
    tone: str
    hook_script: str
    main_script: str
    cta_text: str
```

### AdMetrics
```python
@dataclass
class AdMetrics:
    ad_id: str
    campaign_id: str
    spend: float
    budget: float
    impressions: int
    clicks: int
    conversions: int
    revenue: float
    ctr: float
    cvr: float
    cpa: float
    roas: float
    hours_running: int
    last_conversion: Optional[datetime]
```

### KillDecision
```python
@dataclass
class KillDecision:
    ad_id: str
    should_kill: bool
    reason: KillReason
    confidence: float
    waste_prevented: float
    recommendation: str
    metrics_at_kill: Dict
```

---

## Enums

### KillReason
```python
class KillReason(Enum):
    LOW_CTR = "low_ctr"
    LOW_CVR = "low_cvr"
    HIGH_CPA = "high_cpa"
    NEGATIVE_ROAS = "negative_roas"
    NO_CONVERSIONS = "no_conversions"
    DECLINING_PERFORMANCE = "declining_performance"
    BUDGET_EXHAUSTED = "budget_exhausted"
    MANUAL = "manual"
```

### VariationType
```python
class VariationType(Enum):
    HOOK = "hook"
    CTA = "cta"
    HEADLINE = "headline"
    COLOR = "color"
    MUSIC = "music"
    VOICE = "voice"
    PACING = "pacing"
    DURATION = "duration"
    FORMAT = "format"
```

---

## Key Constants Summary

| Component | Constant | Value | Purpose |
|-----------|----------|-------|---------|
| Motion SDK | WINDOW_SIZE | 30 | Frames per window (1 sec) |
| Motion SDK | FACE_WEIGHT | 3.2 | Face priority multiplier |
| AV Sync | TOLERANCE | 0.1 | Sync tolerance (seconds) |
| Variation Gen | TARGET_VARIATIONS | 50 | Variations per concept |
| Kill Switch | MIN_CTR | 0.005 | 0.5% minimum CTR |
| Kill Switch | MIN_CVR | 0.005 | 0.5% minimum CVR |
| Kill Switch | MIN_ROAS | 0.5 | Minimum ROAS before kill |
| Kill Switch | NO_CONVERSION_SPEND | 100 | $ limit with 0 conversions |
| Budget Opt | SCALE_ROAS | 3.0 | ROAS to trigger scale up |
| Budget Opt | MIN_SPEND | 50 | $ before making decisions |

---

*Generated by Agent 133 - Function Reference Documentation*
