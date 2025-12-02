# Shared Configuration Files

This directory contains configuration files used across all services in the AI Ad Intelligence & Creation Suite.

## Configuration Files

### scene_ranking.yaml
Controls how video scenes are ranked and selected for ad creation.

**Key sections:**
- `weights`: Relative importance of different scene features (motion, objects, text, etc.)
- `thresholds`: Minimum/maximum values for filtering scenes
- `ranking`: Default parameters for scene selection

**Usage:** Loaded by `drive-intel` service for scene scoring and ranking.

### hook_templates.json
Defines text overlay templates for different phases of ad creative.

**Key sections:**
- `templates`: Array of template objects with patterns for Hook, Proof, and CTA phases
- `overlay_styles`: Visual styling for each phase (font size, color, animations)

**Usage:** Used by `video-agent` service for overlay generation during rendering.

### weights.yaml
Version-controlled weights for the predictive scoring engine.

**Key sections:**
- `psychology_weights`: Weights for psychology-based triggers (pain points, transformation, etc.)
- `hook_weights`: Weights for hook strength calculation
- `technical_weights`: Weights for technical quality assessment
- `demographic_weights`: Weights for persona matching
- `novelty_weights`: Weights for semantic uniqueness
- `probability_bands`: CTR prediction bands (low/mid/high)
- `learning`: Parameters for automated weight updates

**Usage:** Loaded by `gateway-api` service for scoring. Updated by nightly learning loop.

### triggers_config.json
Keyword lists for driver-based content analysis.

**Key sections:**
- `driver_keywords`: Keywords grouped by psychology drivers (pain points, transformations, urgency, authority, social proof)
- `fitness_triggers`: Keywords specific to fitness vertical (weight loss, muscle gain, performance, health)

**Usage:** Used by `gateway-api` service for psychology scoring and content classification.

### personas.json
Target audience personas with characteristics and preferences.

**Key sections:**
- `personas`: Array of persona objects with:
  - `id`: Unique identifier
  - `name`: Human-readable name
  - `age_range`: Target age range
  - `fitness_level`: Fitness experience level
  - `keywords`: Keywords that resonate with this persona
  - `pain_points`: Common problems/frustrations
  - `goals`: Desired outcomes

**Usage:** Used by `gateway-api` service for demographic matching and persona fit scoring.

## Editing Configuration

1. **scene_ranking.yaml**: Adjust weights to change which scene features are prioritized
2. **hook_templates.json**: Add new template patterns or modify overlay styles
3. **weights.yaml**: Tune scoring weights based on performance data (or let learning loop adjust)
4. **triggers_config.json**: Expand keyword lists as you discover new high-performing terms
5. **personas.json**: Add new personas or refine existing ones based on audience insights

## Version Control

- All config files are version-controlled in git
- `weights.yaml` includes a version field that gets updated by the learning loop
- Keep a changelog of significant manual changes to config files
