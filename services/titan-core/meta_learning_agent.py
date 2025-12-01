"""
Meta Learning Agent - Real-time learning from Meta Ads campaigns
Fetches actual performance data and updates knowledge base automatically
"""
import os
import json
import logging
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

# Import ML-based hook classifier
try:
    from .engines.hook_classifier import get_hook_classifier
    HOOK_CLASSIFIER_AVAILABLE = True
except ImportError:
    HOOK_CLASSIFIER_AVAILABLE = False
    logging.warning("HookClassifier not available - falling back to keyword-based analysis")

logger = logging.getLogger(__name__)

class MetaLearningAgent:
    """
    Connects to Meta Ads API v19.0 and extracts winning patterns from real campaign data.
    Updates the knowledge base with insights from YOUR actual performance metrics.
    """

    def __init__(self):
        """Initialize Meta Learning Agent with API credentials"""
        self.api_version = "v19.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

        # Load credentials from environment
        self.access_token = os.getenv("META_ACCESS_TOKEN")
        self.ad_account_id = os.getenv("META_AD_ACCOUNT_ID")
        self.app_id = os.getenv("META_APP_ID")
        self.app_secret = os.getenv("META_APP_SECRET")

        if not self.access_token or not self.ad_account_id:
            logger.warning(
                "Meta credentials not configured. Set META_ACCESS_TOKEN and META_AD_ACCOUNT_ID "
                "environment variables to enable learning from real campaign data."
            )

        # Path to knowledge base
        self.knowledge_path = Path(__file__).parent.parent / "shared" / "config"

        logger.info("✅ Meta Learning Agent initialized")

    def fetch_campaign_insights(
        self,
        days_back: int = 30,
        min_spend: float = 10.0
    ) -> Dict[str, Any]:
        """
        Fetch performance insights from Meta Ads for the last N days.

        Args:
            days_back: Number of days to look back (default: 30)
            min_spend: Minimum spend threshold to include campaign (default: $10)

        Returns:
            Dictionary with campaign insights and performance metrics
        """
        if not self.access_token or not self.ad_account_id:
            logger.error("Meta credentials not configured")
            return {"error": "META_ACCESS_TOKEN or META_AD_ACCOUNT_ID not set"}

        try:
            # Date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Meta Ads Insights API parameters
            params = {
                'access_token': self.access_token,
                'fields': ','.join([
                    'campaign_name',
                    'campaign_id',
                    'adset_name',
                    'ad_name',
                    'spend',
                    'impressions',
                    'clicks',
                    'cpm',
                    'ctr',
                    'cpc',
                    'actions',
                    'action_values',
                    'purchase_roas',
                    'cost_per_action_type',
                    'video_30_sec_watched_actions',
                    'video_avg_time_watched_actions',
                    'video_p25_watched_actions',
                    'video_p50_watched_actions',
                    'video_p75_watched_actions',
                    'video_p100_watched_actions'
                ]),
                'level': 'ad',
                'time_range': json.dumps({
                    'since': start_date.strftime('%Y-%m-%d'),
                    'until': end_date.strftime('%Y-%m-%d')
                }),
                'limit': 100,
                'filtering': json.dumps([
                    {'field': 'spend', 'operator': 'GREATER_THAN', 'value': min_spend}
                ])
            }

            # Make API request
            url = f"{self.base_url}/{self.ad_account_id}/insights"
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()

            logger.info(f"✅ Fetched {len(data.get('data', []))} campaign insights from Meta")

            return {
                'success': True,
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                },
                'campaigns': data.get('data', []),
                'total_campaigns': len(data.get('data', [])),
                'fetched_at': datetime.utcnow().isoformat()
            }

        except requests.RequestException as e:
            logger.error(f"Meta API request failed: {e}")
            return {
                'error': str(e),
                'success': False
            }
        except Exception as e:
            logger.error(f"Failed to fetch campaign insights: {e}", exc_info=True)
            return {
                'error': str(e),
                'success': False
            }

    def extract_winning_patterns(self, insights_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze campaign data and extract patterns from winning ads.

        Identifies:
        - Hook types that drive highest CTR
        - Video lengths that perform best
        - Color schemes from top ROAS ads
        - CTA styles that convert
        - Optimal ad format (video vs image vs carousel)

        Args:
            insights_data: Campaign insights from fetch_campaign_insights()

        Returns:
            Dictionary with extracted patterns and recommendations
        """
        if not insights_data.get('success') or not insights_data.get('campaigns'):
            logger.warning("No campaign data to analyze")
            return {'patterns': [], 'insights': 'No data available'}

        campaigns = insights_data['campaigns']

        # Initialize pattern analysis
        patterns = {
            'top_performers': [],
            'hook_patterns': {},
            'video_performance': {
                'optimal_length': None,
                'completion_rates': []
            },
            'ctr_analysis': {
                'high_ctr_ads': [],
                'avg_ctr': 0.0
            },
            'roas_analysis': {
                'high_roas_ads': [],
                'avg_roas': 0.0
            },
            'recommendations': []
        }

        # Analyze each campaign
        total_ctr = 0.0
        total_roas = 0.0
        valid_ctr_count = 0
        valid_roas_count = 0

        for campaign in campaigns:
            try:
                # Extract metrics
                spend = float(campaign.get('spend', 0))
                impressions = int(campaign.get('impressions', 0))
                clicks = int(campaign.get('clicks', 0))
                ctr = float(campaign.get('ctr', 0))

                # Calculate CTR if not provided
                if ctr == 0 and impressions > 0:
                    ctr = (clicks / impressions) * 100

                if ctr > 0:
                    total_ctr += ctr
                    valid_ctr_count += 1

                # Extract ROAS
                roas_data = campaign.get('purchase_roas', [])
                if isinstance(roas_data, list) and len(roas_data) > 0:
                    roas = float(roas_data[0].get('value', 0))
                elif isinstance(roas_data, str):
                    roas = float(roas_data)
                else:
                    roas = 0.0

                if roas > 0:
                    total_roas += roas
                    valid_roas_count += 1

                # Identify high performers (CTR > 2% or ROAS > 3x)
                if ctr > 2.0 or roas > 3.0:
                    patterns['top_performers'].append({
                        'campaign_name': campaign.get('campaign_name', 'Unknown'),
                        'ad_name': campaign.get('ad_name', 'Unknown'),
                        'spend': spend,
                        'ctr': ctr,
                        'roas': roas,
                        'impressions': impressions,
                        'clicks': clicks
                    })

                # High CTR ads (top 20%)
                if ctr > 1.5:
                    patterns['ctr_analysis']['high_ctr_ads'].append({
                        'ad_name': campaign.get('ad_name', 'Unknown'),
                        'ctr': ctr
                    })

                # High ROAS ads (ROAS > 2x)
                if roas > 2.0:
                    patterns['roas_analysis']['high_roas_ads'].append({
                        'ad_name': campaign.get('ad_name', 'Unknown'),
                        'roas': roas
                    })

                # Video performance analysis
                video_p100 = campaign.get('video_p100_watched_actions', [])
                if video_p100 and len(video_p100) > 0:
                    completion_rate = float(video_p100[0].get('value', 0)) / impressions if impressions > 0 else 0
                    patterns['video_performance']['completion_rates'].append(completion_rate * 100)

            except Exception as e:
                logger.warning(f"Error analyzing campaign: {e}")
                continue

        # Calculate averages
        patterns['ctr_analysis']['avg_ctr'] = total_ctr / valid_ctr_count if valid_ctr_count > 0 else 0.0
        patterns['roas_analysis']['avg_roas'] = total_roas / valid_roas_count if valid_roas_count > 0 else 0.0

        # Sort top performers by ROAS
        patterns['top_performers'].sort(key=lambda x: x.get('roas', 0), reverse=True)

        # Generate recommendations based on data
        patterns['recommendations'] = self._generate_recommendations(patterns)

        # Extract hook patterns from top performers
        patterns['hook_patterns'] = self._analyze_hook_patterns(patterns['top_performers'])

        logger.info(f"✅ Extracted patterns from {len(campaigns)} campaigns")
        logger.info(f"   - Top performers: {len(patterns['top_performers'])}")
        logger.info(f"   - Avg CTR: {patterns['ctr_analysis']['avg_ctr']:.2f}%")
        logger.info(f"   - Avg ROAS: {patterns['roas_analysis']['avg_roas']:.2f}x")

        return patterns

    def _analyze_hook_patterns(self, top_performers: List[Dict]) -> Dict[str, Any]:
        """
        Analyze ad names to detect hook patterns using ML-based classification.
        Falls back to keyword-based analysis if ML classifier is not available.
        """
        if HOOK_CLASSIFIER_AVAILABLE and len(top_performers) > 0:
            # Use ML-based hook classification
            try:
                classifier = get_hook_classifier()

                # Extract ad names/hooks from top performers
                hooks = [ad.get('ad_name', '') or ad.get('campaign_name', '')
                        for ad in top_performers]
                hooks = [h for h in hooks if h]  # Filter empty

                if not hooks:
                    logger.warning("No ad names found in top performers")
                    return self._fallback_keyword_analysis(top_performers)

                # Analyze hooks using ML classifier
                logger.info(f"🤖 Analyzing {len(hooks)} hooks with ML classifier...")
                analysis = classifier.analyze_top_performer_hooks(hooks)

                # Convert to the expected format with additional ML insights
                hook_patterns = analysis.get('hook_type_distribution', {})

                # Add ML-specific metadata
                hook_patterns['_ml_analysis'] = {
                    'avg_confidence': analysis.get('avg_confidence', 0.0),
                    'avg_strength': analysis.get('avg_strength', 0.0),
                    'dominant_pattern': analysis.get('dominant_pattern'),
                    'top_patterns': analysis.get('top_patterns', []),
                    'ml_recommendations': analysis.get('recommendations', []),
                    'total_analyzed': analysis.get('total_hooks_analyzed', 0)
                }

                logger.info(f"✅ ML Hook Analysis: Dominant pattern is '{analysis.get('dominant_pattern')}'")
                logger.info(f"   - Avg confidence: {analysis.get('avg_confidence', 0):.2f}")
                logger.info(f"   - Avg strength: {analysis.get('avg_strength', 0):.2f}")

                return hook_patterns

            except Exception as e:
                logger.warning(f"ML classifier failed, falling back to keywords: {e}")
                return self._fallback_keyword_analysis(top_performers)
        else:
            # Fallback to keyword-based analysis
            return self._fallback_keyword_analysis(top_performers)

    def _fallback_keyword_analysis(self, top_performers: List[Dict]) -> Dict[str, Any]:
        """Keyword-based hook analysis (fallback when ML is unavailable)"""
        hook_patterns = {
            'transformation': 0,
            'question': 0,
            'negative_hook': 0,
            'urgency_scarcity': 0,
            'social_proof': 0,
            'curiosity_gap': 0,
            'pattern_interrupt': 0,
            'story_hook': 0,
            'statistic_hook': 0,
            'controversy_hook': 0
        }

        # Keywords for each hook type (expanded to match classifier types)
        transformation_keywords = ['before', 'after', 'transform', 'change', 'result', 'from', 'to']
        question_keywords = ['?', 'how', 'what', 'why', 'when', 'can you', 'do you']
        negative_keywords = ['stop', 'dont', "don't", 'never', 'avoid', 'mistake', 'wrong']
        urgency_keywords = ['now', 'today', 'limited', 'hurry', 'fast', 'urgent', 'expires']
        social_proof_keywords = ['client', 'testimonial', 'review', 'success', 'result', 'customer']
        curiosity_keywords = ['secret', 'discover', 'reveal', 'shocking', 'believe', 'hidden']
        pattern_interrupt_keywords = ['stop', 'wait', 'attention', 'listen', 'breaking']
        story_keywords = ['story', 'journey', 'experience', 'happened', 'remember']
        statistic_keywords = ['%', '$', 'million', 'thousand', 'study', 'proven', 'data']
        controversy_keywords = ['wrong', 'lie', 'truth', 'controversial', 'against', 'myth']

        for ad in top_performers:
            ad_name = ad.get('ad_name', '').lower()
            campaign_name = ad.get('campaign_name', '').lower()
            combined_text = f"{ad_name} {campaign_name}"

            if any(kw in combined_text for kw in transformation_keywords):
                hook_patterns['transformation'] += 1
            if any(kw in combined_text for kw in question_keywords):
                hook_patterns['question'] += 1
            if any(kw in combined_text for kw in negative_keywords):
                hook_patterns['negative_hook'] += 1
            if any(kw in combined_text for kw in urgency_keywords):
                hook_patterns['urgency_scarcity'] += 1
            if any(kw in combined_text for kw in social_proof_keywords):
                hook_patterns['social_proof'] += 1
            if any(kw in combined_text for kw in curiosity_keywords):
                hook_patterns['curiosity_gap'] += 1
            if any(kw in combined_text for kw in pattern_interrupt_keywords):
                hook_patterns['pattern_interrupt'] += 1
            if any(kw in combined_text for kw in story_keywords):
                hook_patterns['story_hook'] += 1
            if any(kw in combined_text for kw in statistic_keywords):
                hook_patterns['statistic_hook'] += 1
            if any(kw in combined_text for kw in controversy_keywords):
                hook_patterns['controversy_hook'] += 1

        hook_patterns['_ml_analysis'] = {
            'method': 'keyword_fallback',
            'note': 'Using keyword-based analysis (ML classifier not available)'
        }

        return hook_patterns

    def _generate_recommendations(self, patterns: Dict) -> List[str]:
        """Generate actionable recommendations based on patterns"""
        recommendations = []

        avg_ctr = patterns['ctr_analysis']['avg_ctr']
        avg_roas = patterns['roas_analysis']['avg_roas']

        if avg_ctr < 1.0:
            recommendations.append("⚠️ CTR below 1% - Focus on stronger hooks and pattern interrupts")
        elif avg_ctr > 2.0:
            recommendations.append("✅ Strong CTR performance - Your hooks are working well")

        if avg_roas < 2.0:
            recommendations.append("⚠️ ROAS below 2x - Optimize targeting and offer strength")
        elif avg_roas > 3.0:
            recommendations.append("✅ Excellent ROAS - Scale winning campaigns")

        # Hook pattern recommendations with ML insights
        hook_patterns = patterns.get('hook_patterns', {})
        if hook_patterns:
            # Check if ML analysis is available
            ml_analysis = hook_patterns.get('_ml_analysis', {})

            if ml_analysis.get('ml_recommendations'):
                # Use ML-generated recommendations
                recommendations.extend(ml_analysis['ml_recommendations'])
            else:
                # Fallback to basic hook pattern analysis
                # Filter out metadata keys
                pattern_counts = {k: v for k, v in hook_patterns.items() if not k.startswith('_')}
                if pattern_counts:
                    top_hook = max(pattern_counts.items(), key=lambda x: x[1])
                    recommendations.append(f"📊 Your best-performing hook type: '{top_hook[0]}' ({top_hook[1]} top ads)")

        # Video completion recommendations
        completion_rates = patterns['video_performance']['completion_rates']
        if completion_rates:
            avg_completion = sum(completion_rates) / len(completion_rates)
            if avg_completion < 25:
                recommendations.append("⚠️ Low video completion - Shorten videos or improve first 3 seconds")
            elif avg_completion > 50:
                recommendations.append("✅ Strong video retention - Your content is engaging")

        return recommendations

    def update_knowledge_base(self, patterns: Dict[str, Any]) -> bool:
        """
        Update the knowledge base with insights from Meta performance data.

        Updates:
        - shared/config/meta_insights.json with latest patterns
        - shared/config/weights.yaml with performance-based adjustments (future)

        Args:
            patterns: Extracted patterns from extract_winning_patterns()

        Returns:
            True if successful, False otherwise
        """
        try:
            # Create meta_insights.json with latest patterns
            insights_file = self.knowledge_path / "meta_insights.json"

            # Ensure directory exists
            self.knowledge_path.mkdir(parents=True, exist_ok=True)

            # Prepare insights data
            insights = {
                'last_updated': datetime.utcnow().isoformat(),
                'patterns': patterns,
                'version': '1.0.0'
            }

            # Write to file
            with open(insights_file, 'w') as f:
                json.dump(insights, f, indent=2)

            logger.info(f"✅ Knowledge base updated: {insights_file}")

            # Trigger knowledge base reload (if using hot-reload)
            try:
                from knowledge.core import titan_knowledge
                if titan_knowledge:
                    titan_knowledge.reload()
                    logger.info("✅ TitanKnowledge reloaded with new insights")
            except Exception as e:
                logger.warning(f"Could not reload TitanKnowledge: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to update knowledge base: {e}", exc_info=True)
            return False

    def run_learning_cycle(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Execute a complete learning cycle:
        1. Fetch latest Meta campaign data
        2. Extract winning patterns
        3. Update knowledge base

        Args:
            days_back: Number of days to analyze (default: 30)

        Returns:
            Dictionary with cycle results and insights
        """
        logger.info(f"🧠 Starting Meta learning cycle (last {days_back} days)...")

        # Step 1: Fetch campaign insights
        insights_data = self.fetch_campaign_insights(days_back=days_back)

        if not insights_data.get('success'):
            return {
                'success': False,
                'error': insights_data.get('error', 'Unknown error'),
                'message': 'Failed to fetch Meta campaign data'
            }

        # Step 2: Extract patterns
        patterns = self.extract_winning_patterns(insights_data)

        # Step 3: Update knowledge base
        update_success = self.update_knowledge_base(patterns)

        # Generate summary
        result = {
            'success': True,
            'campaigns_analyzed': insights_data.get('total_campaigns', 0),
            'top_performers': len(patterns.get('top_performers', [])),
            'avg_ctr': patterns['ctr_analysis']['avg_ctr'],
            'avg_roas': patterns['roas_analysis']['avg_roas'],
            'recommendations': patterns.get('recommendations', []),
            'knowledge_base_updated': update_success,
            'timestamp': datetime.utcnow().isoformat()
        }

        logger.info("✅ Meta learning cycle complete")
        logger.info(f"   - Campaigns analyzed: {result['campaigns_analyzed']}")
        logger.info(f"   - Top performers: {result['top_performers']}")
        logger.info(f"   - Avg CTR: {result['avg_ctr']:.2f}%")
        logger.info(f"   - Avg ROAS: {result['avg_roas']:.2f}x")

        return result


# Singleton instance
meta_learning_agent = MetaLearningAgent()
