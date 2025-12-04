import torch
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    pipeline
)
import numpy as np
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class HookType(Enum):
    CURIOSITY_GAP = "curiosity_gap"
    TRANSFORMATION = "transformation"
    URGENCY_SCARCITY = "urgency_scarcity"
    SOCIAL_PROOF = "social_proof"
    PATTERN_INTERRUPT = "pattern_interrupt"
    QUESTION = "question"
    NEGATIVE_HOOK = "negative_hook"
    STORY_HOOK = "story_hook"
    STATISTIC_HOOK = "statistic_hook"
    CONTROVERSY_HOOK = "controversy_hook"
    BENEFIT_STACK = "benefit_stack"
    PAIN_AGITATE = "pain_agitate"


@dataclass
class HookResult:
    text: str
    primary_hook_type: HookType
    hook_types: List[Tuple[HookType, float]]  # type, confidence
    hook_strength: float  # 0-1
    sentiment: str  # positive, negative, neutral
    sentiment_score: float
    attention_score: float
    improvement_suggestions: List[str] = field(default_factory=list)


@dataclass
class HookAnalysis:
    hooks_detected: int
    primary_hook: HookType
    hook_distribution: Dict[str, float]
    avg_hook_strength: float
    strongest_hook_text: str
    weakest_hook_text: str


class PretrainedHookDetector:
    """BERT/RoBERTa-based hook detection for ad copy."""

    # Pretrained models to use
    SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    CLASSIFICATION_MODEL = "facebook/bart-large-mnli"  # Zero-shot

    # Hook type descriptions for zero-shot classification
    HOOK_TYPE_LABELS = {
        HookType.CURIOSITY_GAP: "This text creates curiosity or mystery that makes you want to learn more",
        HookType.TRANSFORMATION: "This text promises a transformation or dramatic change in results",
        HookType.URGENCY_SCARCITY: "This text emphasizes urgency, scarcity, or limited time offers",
        HookType.SOCIAL_PROOF: "This text uses testimonials, statistics, or social validation",
        HookType.PATTERN_INTERRUPT: "This text breaks patterns with unexpected or surprising statements",
        HookType.QUESTION: "This text uses a compelling question to engage the reader",
        HookType.NEGATIVE_HOOK: "This text addresses problems, pain points, or negative emotions",
        HookType.STORY_HOOK: "This text uses storytelling or narrative techniques",
        HookType.STATISTIC_HOOK: "This text uses numbers, data, or statistics to grab attention",
        HookType.CONTROVERSY_HOOK: "This text uses controversial or contrarian viewpoints",
        HookType.BENEFIT_STACK: "This text stacks multiple benefits or value propositions",
        HookType.PAIN_AGITATE: "This text agitates a pain point before offering a solution",
    }

    def __init__(
        self,
        device: str = None,  # auto-detect cuda/cpu
        cache_dir: str = None
    ):
        """Initialize with pretrained models."""
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.cache_dir = cache_dir
        self.tokenizer = None
        self.sentiment_pipeline = None
        self.classification_pipeline = None

        logger.info(f"Initializing PretrainedHookDetector on device: {self.device}")
        self._load_models(cache_dir)

    def _load_models(self, cache_dir: str = None) -> None:
        """Load pretrained models from HuggingFace."""
        try:
            logger.info(f"Loading sentiment model: {self.SENTIMENT_MODEL}")
            self.sentiment_pipeline = pipeline(
                "sentiment-analysis",
                model=self.SENTIMENT_MODEL,
                device=0 if self.device == "cuda" else -1,
                cache_dir=cache_dir
            )

            logger.info(f"Loading zero-shot classification model: {self.CLASSIFICATION_MODEL}")
            self.classification_pipeline = pipeline(
                "zero-shot-classification",
                model=self.CLASSIFICATION_MODEL,
                device=0 if self.device == "cuda" else -1,
                cache_dir=cache_dir
            )

            logger.info("Models loaded successfully")

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            raise

    # Hook Detection
    def detect_hook(
        self,
        text: str,
        threshold: float = 0.3
    ) -> HookResult:
        """Detect hook type and strength in text."""
        try:
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")

            # Classify hook types
            hook_types = self.classify_hook_type(text)

            # Filter by threshold
            filtered_hooks = [(ht, score) for ht, score in hook_types if score >= threshold]

            if not filtered_hooks:
                # Use the highest scoring hook even if below threshold
                filtered_hooks = [hook_types[0]] if hook_types else [(HookType.QUESTION, 0.1)]

            primary_hook_type = filtered_hooks[0][0]

            # Score hook strength
            hook_strength = self.score_hook_strength(text)

            # Analyze sentiment
            sentiment, sentiment_score = self.analyze_sentiment(text)

            # Calculate attention score
            attention_score = self._calculate_attention_score(text)

            # Generate improvement suggestions
            suggestions = self.suggest_improvement(text, primary_hook_type)

            return HookResult(
                text=text,
                primary_hook_type=primary_hook_type,
                hook_types=filtered_hooks,
                hook_strength=hook_strength,
                sentiment=sentiment,
                sentiment_score=sentiment_score,
                attention_score=attention_score,
                improvement_suggestions=suggestions
            )

        except Exception as e:
            logger.error(f"Error detecting hook: {e}")
            raise

    def detect_hooks_batch(
        self,
        texts: List[str],
        threshold: float = 0.3
    ) -> List[HookResult]:
        """Batch hook detection."""
        try:
            results = []
            for text in texts:
                try:
                    result = self.detect_hook(text, threshold)
                    results.append(result)
                except Exception as e:
                    logger.warning(f"Error processing text '{text[:50]}...': {e}")
                    # Add a default result for failed texts
                    results.append(HookResult(
                        text=text,
                        primary_hook_type=HookType.QUESTION,
                        hook_types=[(HookType.QUESTION, 0.1)],
                        hook_strength=0.1,
                        sentiment="neutral",
                        sentiment_score=0.5,
                        attention_score=0.1,
                        improvement_suggestions=["Error processing text"]
                    ))

            return results

        except Exception as e:
            logger.error(f"Error in batch detection: {e}")
            raise

    def classify_hook_type(
        self,
        text: str
    ) -> List[Tuple[HookType, float]]:
        """Classify text into hook types with confidence."""
        try:
            # Prepare labels for zero-shot classification
            candidate_labels = list(self.HOOK_TYPE_LABELS.values())

            # Run zero-shot classification
            result = self.classification_pipeline(
                text,
                candidate_labels,
                multi_label=True
            )

            # Map results back to HookType enum
            hook_scores = []
            label_to_hook_type = {v: k for k, v in self.HOOK_TYPE_LABELS.items()}

            for label, score in zip(result['labels'], result['scores']):
                hook_type = label_to_hook_type.get(label)
                if hook_type:
                    hook_scores.append((hook_type, float(score)))

            # Sort by score descending
            hook_scores.sort(key=lambda x: x[1], reverse=True)

            return hook_scores

        except Exception as e:
            logger.error(f"Error classifying hook type: {e}")
            # Return default classification
            return [(HookType.QUESTION, 0.5)]

    # Hook Strength
    def score_hook_strength(
        self,
        text: str
    ) -> float:
        """Score hook strength from 0-1."""
        try:
            # Combine multiple factors
            attention = self._calculate_attention_score(text)
            curiosity = self._calculate_curiosity_score(text)

            # Get sentiment intensity
            _, sentiment_score = self.analyze_sentiment(text)
            sentiment_intensity = abs(sentiment_score - 0.5) * 2  # 0-1 range

            # Weighted combination
            strength = (
                attention * 0.4 +
                curiosity * 0.4 +
                sentiment_intensity * 0.2
            )

            return min(1.0, max(0.0, strength))

        except Exception as e:
            logger.error(f"Error scoring hook strength: {e}")
            return 0.5

    def _calculate_attention_score(
        self,
        text: str
    ) -> float:
        """Calculate attention-grabbing score."""
        try:
            score = 0.0
            text_lower = text.lower()

            # Power words
            power_words = [
                'secret', 'proven', 'amazing', 'revolutionary', 'discover',
                'unlock', 'guaranteed', 'instant', 'exclusive', 'limited',
                'breakthrough', 'insider', 'hidden', 'forbidden', 'banned'
            ]
            power_word_count = sum(1 for word in power_words if word in text_lower)
            score += min(0.3, power_word_count * 0.1)

            # Exclamation marks
            exclamation_count = text.count('!')
            score += min(0.2, exclamation_count * 0.1)

            # Questions
            if '?' in text:
                score += 0.15

            # Numbers/statistics
            if re.search(r'\d+[%$]?|\d+x', text):
                score += 0.15

            # Capital words (but not all caps)
            capital_words = re.findall(r'\b[A-Z]{2,}\b', text)
            if capital_words and len(capital_words) <= 3:
                score += 0.1

            # Emotional words
            emotional_words = [
                'love', 'hate', 'fear', 'shocking', 'incredible', 'devastating',
                'beautiful', 'ugly', 'perfect', 'terrible', 'nightmare', 'dream'
            ]
            emotional_count = sum(1 for word in emotional_words if word in text_lower)
            score += min(0.15, emotional_count * 0.05)

            return min(1.0, score)

        except Exception as e:
            logger.error(f"Error calculating attention score: {e}")
            return 0.5

    def _calculate_curiosity_score(
        self,
        text: str
    ) -> float:
        """Calculate curiosity-inducing score."""
        try:
            score = 0.0
            text_lower = text.lower()

            # Curiosity gap phrases
            curiosity_phrases = [
                'you won\'t believe', 'what happened next', 'the secret',
                'never told you', 'don\'t want you to know', 'hidden truth',
                'what if', 'imagine', 'picture this', 'here\'s why',
                'the reason', 'find out', 'discover', 'revealed'
            ]

            for phrase in curiosity_phrases:
                if phrase in text_lower:
                    score += 0.2

            # Mystery/intrigue words
            mystery_words = ['mystery', 'secret', 'unknown', 'hidden', 'untold']
            mystery_count = sum(1 for word in mystery_words if word in text_lower)
            score += min(0.3, mystery_count * 0.15)

            # Incomplete information markers
            if '...' in text:
                score += 0.15

            # Questions
            question_count = text.count('?')
            score += min(0.25, question_count * 0.1)

            return min(1.0, score)

        except Exception as e:
            logger.error(f"Error calculating curiosity score: {e}")
            return 0.5

    # Sentiment Analysis
    def analyze_sentiment(
        self,
        text: str
    ) -> Tuple[str, float]:
        """Analyze sentiment of hook."""
        try:
            result = self.sentiment_pipeline(text)[0]
            label = result['label'].lower()
            score = float(result['score'])

            # Map to standard sentiment labels
            if 'pos' in label or 'positive' in label:
                sentiment = 'positive'
            elif 'neg' in label or 'negative' in label:
                sentiment = 'negative'
            else:
                sentiment = 'neutral'

            return sentiment, score

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return 'neutral', 0.5

    # Improvement Suggestions
    def suggest_improvement(
        self,
        text: str,
        target_hook_type: HookType = None
    ) -> List[str]:
        """Suggest improvements for hook."""
        try:
            suggestions = []
            text_lower = text.lower()

            # Length check
            word_count = len(text.split())
            if word_count < 5:
                suggestions.append("Hook is too short - aim for 5-15 words for optimal impact")
            elif word_count > 20:
                suggestions.append("Hook is too long - try to be more concise (under 15 words)")

            # Power word check
            power_words = ['secret', 'proven', 'amazing', 'discover', 'unlock', 'guaranteed']
            if not any(word in text_lower for word in power_words):
                suggestions.append("Consider adding power words like 'discover', 'proven', or 'unlock'")

            # Specificity check (numbers)
            if not re.search(r'\d', text):
                suggestions.append("Add specific numbers or statistics to increase credibility")

            # Question check
            if '?' not in text and target_hook_type == HookType.QUESTION:
                suggestions.append("Add a compelling question to engage readers")

            # Emotional intensity
            sentiment, score = self.analyze_sentiment(text)
            if score < 0.7:
                suggestions.append("Increase emotional intensity with stronger language")

            # Call to action/curiosity
            curiosity_score = self._calculate_curiosity_score(text)
            if curiosity_score < 0.4:
                suggestions.append("Create more curiosity gap - leave something for the reader to discover")

            # Hook type specific suggestions
            if target_hook_type:
                if target_hook_type == HookType.URGENCY_SCARCITY:
                    if not any(word in text_lower for word in ['now', 'today', 'limited', 'hurry', 'expires']):
                        suggestions.append("Add urgency words like 'now', 'limited time', or 'today only'")

                elif target_hook_type == HookType.SOCIAL_PROOF:
                    if not re.search(r'\d+\s*(people|users|customers|clients)', text_lower):
                        suggestions.append("Include specific numbers of satisfied customers or users")

                elif target_hook_type == HookType.TRANSFORMATION:
                    if 'from' not in text_lower or 'to' not in text_lower:
                        suggestions.append("Show clear before/after transformation (from X to Y)")

            if not suggestions:
                suggestions.append("Hook is strong - minor tweaks to test different variations")

            return suggestions

        except Exception as e:
            logger.error(f"Error suggesting improvements: {e}")
            return ["Unable to generate suggestions"]

    def generate_hook_variants(
        self,
        text: str,
        num_variants: int = 3
    ) -> List[str]:
        """Generate hook variations."""
        try:
            variants = []

            # Variant 1: Add question
            if '?' not in text:
                variants.append(f"What if {text.lower()}?")

            # Variant 2: Add urgency
            urgency_prefixes = ["Don't miss:", "Limited time:", "Act now:"]
            if len(variants) < num_variants:
                variants.append(f"{urgency_prefixes[0]} {text}")

            # Variant 3: Add curiosity gap
            curiosity_prefixes = ["Discover how", "The secret to", "Learn why"]
            if len(variants) < num_variants:
                variants.append(f"{curiosity_prefixes[0]} {text.lower()}")

            # Variant 4: Add social proof
            if len(variants) < num_variants:
                variants.append(f"10,000+ people use: {text}")

            # Variant 5: Add statistics
            if len(variants) < num_variants:
                variants.append(f"3X your results: {text}")

            return variants[:num_variants]

        except Exception as e:
            logger.error(f"Error generating variants: {e}")
            return [text]

    # Batch Analysis
    def analyze_hooks(
        self,
        texts: List[str]
    ) -> HookAnalysis:
        """Analyze hooks across multiple texts."""
        try:
            if not texts:
                raise ValueError("No texts provided for analysis")

            results = self.detect_hooks_batch(texts)

            # Count hooks
            hooks_detected = len(results)

            # Get primary hooks distribution
            hook_counter = Counter([r.primary_hook_type for r in results])
            total = len(results)
            hook_distribution = {
                hook_type.value: count / total
                for hook_type, count in hook_counter.items()
            }

            # Get most common primary hook
            primary_hook = hook_counter.most_common(1)[0][0]

            # Calculate average hook strength
            avg_hook_strength = np.mean([r.hook_strength for r in results])

            # Find strongest and weakest
            sorted_results = sorted(results, key=lambda x: x.hook_strength, reverse=True)
            strongest_hook_text = sorted_results[0].text
            weakest_hook_text = sorted_results[-1].text

            return HookAnalysis(
                hooks_detected=hooks_detected,
                primary_hook=primary_hook,
                hook_distribution=hook_distribution,
                avg_hook_strength=float(avg_hook_strength),
                strongest_hook_text=strongest_hook_text,
                weakest_hook_text=weakest_hook_text
            )

        except Exception as e:
            logger.error(f"Error analyzing hooks: {e}")
            raise

    def compare_hooks(
        self,
        hooks: List[str]
    ) -> Dict[str, Any]:
        """Compare multiple hooks."""
        try:
            results = self.detect_hooks_batch(hooks)

            comparison = {
                'hooks': [],
                'best_overall': None,
                'best_attention': None,
                'best_curiosity': None,
                'most_positive': None,
                'most_negative': None,
            }

            for hook, result in zip(hooks, results):
                comparison['hooks'].append({
                    'text': hook,
                    'primary_type': result.primary_hook_type.value,
                    'strength': result.hook_strength,
                    'attention': result.attention_score,
                    'sentiment': result.sentiment,
                    'sentiment_score': result.sentiment_score
                })

            # Find best hooks
            sorted_by_strength = sorted(results, key=lambda x: x.hook_strength, reverse=True)
            sorted_by_attention = sorted(results, key=lambda x: x.attention_score, reverse=True)
            sorted_by_sentiment = sorted(results, key=lambda x: x.sentiment_score, reverse=True)

            comparison['best_overall'] = sorted_by_strength[0].text
            comparison['best_attention'] = sorted_by_attention[0].text

            # Most positive (highest sentiment score)
            comparison['most_positive'] = sorted_by_sentiment[-1].text

            # Most negative (lowest sentiment score)
            comparison['most_negative'] = sorted_by_sentiment[0].text

            # Calculate curiosity for best
            curiosity_scores = [(h, self._calculate_curiosity_score(h)) for h in hooks]
            best_curiosity = max(curiosity_scores, key=lambda x: x[1])
            comparison['best_curiosity'] = best_curiosity[0]

            return comparison

        except Exception as e:
            logger.error(f"Error comparing hooks: {e}")
            raise

    def rank_hooks(
        self,
        hooks: List[str],
        metric: str = "strength"
    ) -> List[Tuple[str, float]]:
        """Rank hooks by metric."""
        try:
            if metric not in ['strength', 'attention', 'curiosity', 'sentiment']:
                raise ValueError(f"Invalid metric: {metric}. Choose from: strength, attention, curiosity, sentiment")

            if metric == 'strength':
                results = self.detect_hooks_batch(hooks)
                ranked = [(r.text, r.hook_strength) for r in results]

            elif metric == 'attention':
                ranked = [(h, self._calculate_attention_score(h)) for h in hooks]

            elif metric == 'curiosity':
                ranked = [(h, self._calculate_curiosity_score(h)) for h in hooks]

            elif metric == 'sentiment':
                ranked = [(h, self.analyze_sentiment(h)[1]) for h in hooks]

            # Sort by score descending
            ranked.sort(key=lambda x: x[1], reverse=True)

            return ranked

        except Exception as e:
            logger.error(f"Error ranking hooks: {e}")
            raise

    # Patterns
    def extract_hook_patterns(
        self,
        successful_hooks: List[str]
    ) -> Dict[str, Any]:
        """Extract patterns from successful hooks."""
        try:
            if not successful_hooks:
                return {}

            patterns = {
                'common_hook_types': {},
                'avg_length': 0,
                'common_words': [],
                'common_patterns': [],
                'avg_strength': 0.0,
            }

            # Analyze all hooks
            results = self.detect_hooks_batch(successful_hooks)

            # Hook type distribution
            hook_types = [r.primary_hook_type.value for r in results]
            type_counts = Counter(hook_types)
            patterns['common_hook_types'] = dict(type_counts.most_common(5))

            # Average length
            lengths = [len(h.split()) for h in successful_hooks]
            patterns['avg_length'] = int(np.mean(lengths))

            # Average strength
            patterns['avg_strength'] = float(np.mean([r.hook_strength for r in results]))

            # Common words (excluding stop words)
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'is', 'are', 'was', 'were'}
            all_words = []
            for hook in successful_hooks:
                words = re.findall(r'\b\w+\b', hook.lower())
                all_words.extend([w for w in words if w not in stop_words])

            word_counts = Counter(all_words)
            patterns['common_words'] = [word for word, _ in word_counts.most_common(10)]

            # Common patterns
            pattern_list = []

            # Check for questions
            question_ratio = sum(1 for h in successful_hooks if '?' in h) / len(successful_hooks)
            if question_ratio > 0.3:
                pattern_list.append(f"Questions ({question_ratio:.0%})")

            # Check for numbers
            number_ratio = sum(1 for h in successful_hooks if re.search(r'\d', h)) / len(successful_hooks)
            if number_ratio > 0.3:
                pattern_list.append(f"Numbers/Stats ({number_ratio:.0%})")

            # Check for power words
            power_words = ['secret', 'proven', 'amazing', 'discover', 'unlock']
            power_ratio = sum(1 for h in successful_hooks if any(pw in h.lower() for pw in power_words)) / len(successful_hooks)
            if power_ratio > 0.3:
                pattern_list.append(f"Power words ({power_ratio:.0%})")

            patterns['common_patterns'] = pattern_list

            return patterns

        except Exception as e:
            logger.error(f"Error extracting patterns: {e}")
            return {}

    def match_pattern(
        self,
        text: str,
        patterns: List[str]
    ) -> List[Tuple[str, float]]:
        """Match text against known patterns."""
        try:
            matches = []
            text_lower = text.lower()

            for pattern in patterns:
                score = 0.0
                pattern_lower = pattern.lower()

                # Exact phrase match
                if pattern_lower in text_lower:
                    score += 0.5

                # Word overlap
                pattern_words = set(re.findall(r'\b\w+\b', pattern_lower))
                text_words = set(re.findall(r'\b\w+\b', text_lower))
                overlap = len(pattern_words & text_words)
                if pattern_words:
                    score += 0.5 * (overlap / len(pattern_words))

                if score > 0:
                    matches.append((pattern, score))

            # Sort by score descending
            matches.sort(key=lambda x: x[1], reverse=True)

            return matches

        except Exception as e:
            logger.error(f"Error matching patterns: {e}")
            return []

    # Model Info
    def get_model_info(self) -> Dict[str, Any]:
        """Get loaded model information."""
        try:
            info = {
                'sentiment_model': self.SENTIMENT_MODEL,
                'classification_model': self.CLASSIFICATION_MODEL,
                'device': self.device,
                'cache_dir': self.cache_dir,
                'hook_types': [ht.value for ht in HookType],
                'cuda_available': torch.cuda.is_available(),
            }

            if torch.cuda.is_available():
                info['cuda_device_name'] = torch.cuda.get_device_name(0)
                info['cuda_device_count'] = torch.cuda.device_count()

            return info

        except Exception as e:
            logger.error(f"Error getting model info: {e}")
            return {'error': str(e)}

    def warmup(self) -> None:
        """Warmup models with dummy input."""
        try:
            logger.info("Warming up models...")

            dummy_text = "This is a test hook to warm up the models."

            # Warmup sentiment pipeline
            self.sentiment_pipeline(dummy_text)

            # Warmup classification pipeline
            self.classification_pipeline(
                dummy_text,
                list(self.HOOK_TYPE_LABELS.values())[:3]  # Just use a few labels for warmup
            )

            logger.info("Model warmup completed")

        except Exception as e:
            logger.error(f"Error during warmup: {e}")
            raise
