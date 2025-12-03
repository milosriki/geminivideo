"""
BERT-based Hook Pattern Classifier
Classifies video script hooks into 10 distinct pattern types using transformer models
"""
import os
import logging
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import json
from pathlib import Path

try:
    import torch
    from transformers import (
        AutoTokenizer,
        AutoModelForSequenceClassification,
        TrainingArguments,
        Trainer,
        DataCollatorWithPadding
    )
    from torch.utils.data import Dataset
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    logging.warning("transformers or torch not installed - HookClassifier will not work")

logger = logging.getLogger(__name__)


@dataclass
class HookClassification:
    """Result of hook classification"""
    primary_hook: str
    confidence: float
    secondary_hooks: List[Tuple[str, float]]
    all_scores: Dict[str, float]
    hook_strength: float


class HookDataset(Dataset):
    """Dataset for training/fine-tuning hook classifier"""

    def __init__(self, texts: List[str], labels: List[int], tokenizer, max_length: int = 128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = self.texts[idx]
        label = self.labels[idx]

        encoding = self.tokenizer(
            text,
            truncation=True,
            padding='max_length',
            max_length=self.max_length,
            return_tensors='pt'
        )

        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long)
        }


class HookClassifier:
    """
    BERT-based hook pattern classifier for video scripts.

    Classifies hooks into 10 distinct pattern types:
    - curiosity_gap: Creates information gaps that viewers want filled
    - transformation: Shows before/after, results, changes
    - urgency_scarcity: Limited time, exclusive, FOMO-driven
    - social_proof: Testimonials, reviews, client results
    - pattern_interrupt: Unexpected, shocking, breaks expectations
    - question: Direct questions that engage viewer
    - negative_hook: Warns about mistakes, things to avoid
    - story_hook: Narrative-based, personal stories
    - statistic_hook: Data-driven, numbers, percentages
    - controversy_hook: Contrarian, challenges conventional wisdom
    """

    HOOK_TYPES = [
        'curiosity_gap',
        'transformation',
        'urgency_scarcity',
        'social_proof',
        'pattern_interrupt',
        'question',
        'negative_hook',
        'story_hook',
        'statistic_hook',
        'controversy_hook'
    ]

    def __init__(
        self,
        model_name: str = "bert-base-uncased",
        device: Optional[str] = None,
        lazy_load: bool = True,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize hook classifier.

        Args:
            model_name: HuggingFace model name or path to local model
            device: Device to run model on ('cpu', 'cuda', 'mps'). Auto-detects if None
            lazy_load: If True, only loads model when first needed
            cache_dir: Directory to cache models
        """
        if not TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "transformers and torch are required for HookClassifier. "
                "Install with: pip install transformers torch"
            )

        self.model_name = model_name
        self.num_labels = len(self.HOOK_TYPES)
        self.label_to_hook = {i: hook for i, hook in enumerate(self.HOOK_TYPES)}
        self.hook_to_label = {hook: i for i, hook in enumerate(self.HOOK_TYPES)}

        # Device setup
        if device is None:
            if torch.cuda.is_available():
                self.device = 'cuda'
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                self.device = 'mps'
            else:
                self.device = 'cpu'
        else:
            self.device = device

        self.cache_dir = cache_dir or os.path.expanduser("~/.cache/geminivideo/models")
        os.makedirs(self.cache_dir, exist_ok=True)

        # Model and tokenizer (lazy loaded)
        self.tokenizer = None
        self.model = None
        self._model_loaded = False

        if not lazy_load:
            self._load_model()

        logger.info(f"✅ HookClassifier initialized (device: {self.device}, lazy_load: {lazy_load})")

    def _load_model(self):
        """Load model and tokenizer"""
        if self._model_loaded:
            return

        try:
            logger.info(f"Loading model: {self.model_name}")

            # Check if we have a fine-tuned model saved locally
            local_model_path = Path(self.cache_dir) / "hook_classifier_finetuned"

            if local_model_path.exists():
                logger.info(f"Loading fine-tuned model from {local_model_path}")
                model_path = str(local_model_path)
            else:
                logger.info("Loading pre-trained base model (not fine-tuned yet)")
                model_path = self.model_name

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_path if local_model_path.exists() else self.model_name,
                cache_dir=self.cache_dir
            )

            # Load model
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_path,
                num_labels=self.num_labels,
                cache_dir=self.cache_dir
            )

            self.model.to(self.device)
            self.model.eval()

            self._model_loaded = True
            logger.info(f"✅ Model loaded successfully on {self.device}")

        except Exception as e:
            logger.error(f"Failed to load model: {e}", exc_info=True)
            raise

    def classify(self, text: str) -> HookClassification:
        """
        Classify a hook text into pattern types.

        Args:
            text: Hook text to classify

        Returns:
            HookClassification with primary hook, confidence, and all scores
        """
        self._load_model()

        # Tokenize input
        inputs = self.tokenizer(
            text,
            return_tensors='pt',
            truncation=True,
            max_length=128,
            padding=True
        )

        # Move to device
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Get predictions
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)

        # Convert to numpy
        probs_np = probs.cpu().numpy()[0]

        # Get all scores
        all_scores = {
            self.label_to_hook[i]: float(probs_np[i])
            for i in range(self.num_labels)
        }

        # Get top prediction
        primary_idx = int(np.argmax(probs_np))
        primary_hook = self.label_to_hook[primary_idx]
        confidence = float(probs_np[primary_idx])

        # Get secondary hooks (sorted by score, excluding primary)
        sorted_indices = np.argsort(probs_np)[::-1]
        secondary_hooks = [
            (self.label_to_hook[int(idx)], float(probs_np[idx]))
            for idx in sorted_indices[1:4]  # Top 3 secondary
        ]

        # Calculate hook strength
        hook_strength = self._calculate_hook_strength(text, all_scores)

        return HookClassification(
            primary_hook=primary_hook,
            confidence=confidence,
            secondary_hooks=secondary_hooks,
            all_scores=all_scores,
            hook_strength=hook_strength
        )

    def classify_video_script(
        self,
        transcript: str,
        hook_end_marker: Optional[str] = None,
        hook_duration_seconds: float = 3.0
    ) -> Dict[str, Any]:
        """
        Analyze a video script, separating hook from body.

        Args:
            transcript: Full video transcript with timestamps
            hook_end_marker: Optional marker to identify end of hook (e.g., "[3s]")
            hook_duration_seconds: Duration of hook in seconds (default: 3.0)

        Returns:
            Dictionary with hook analysis and body preview
        """
        # Extract hook section
        if hook_end_marker and hook_end_marker in transcript:
            hook_text = transcript.split(hook_end_marker)[0].strip()
        else:
            # Simple heuristic: first 2-3 sentences or first paragraph
            sentences = transcript.split('.')
            hook_text = '. '.join(sentences[:3]).strip()

        # Classify hook
        hook_classification = self.classify(hook_text)

        # Extract body (everything after hook)
        body_text = transcript[len(hook_text):].strip()

        # Analyze hook characteristics
        analysis = {
            'hook': {
                'text': hook_text,
                'classification': {
                    'primary_type': hook_classification.primary_hook,
                    'confidence': hook_classification.confidence,
                    'secondary_types': hook_classification.secondary_hooks,
                    'all_scores': hook_classification.all_scores
                },
                'strength': hook_classification.hook_strength,
                'word_count': len(hook_text.split()),
                'char_count': len(hook_text)
            },
            'body': {
                'preview': body_text[:200] + '...' if len(body_text) > 200 else body_text,
                'word_count': len(body_text.split())
            },
            'hook_to_body_ratio': len(hook_text.split()) / max(len(transcript.split()), 1)
        }

        return analysis

    def _calculate_hook_strength(self, text: str, scores: Dict[str, float]) -> float:
        """
        Calculate overall hook strength based on multiple factors.

        Factors:
        - Confidence of primary classification
        - Presence of multiple hook types (ensemble effect)
        - Text characteristics (length, punctuation, power words)

        Returns:
            Float between 0.0 and 1.0
        """
        # Factor 1: Primary classification confidence
        max_score = max(scores.values())

        # Factor 2: Ensemble effect (multiple strong signals)
        high_scores = [s for s in scores.values() if s > 0.2]
        ensemble_bonus = min(len(high_scores) * 0.05, 0.15)

        # Factor 3: Text characteristics
        text_lower = text.lower()

        # Power words that strengthen hooks
        power_words = [
            'secret', 'proven', 'guaranteed', 'discover', 'reveal',
            'shocking', 'never', 'always', 'instantly', 'breakthrough',
            'exclusive', 'insider', 'hack', 'trick', 'mistake',
            'warning', 'urgent', 'limited', 'now', 'today'
        ]

        power_word_count = sum(1 for word in power_words if word in text_lower)
        power_word_bonus = min(power_word_count * 0.03, 0.1)

        # Question marks strengthen engagement
        question_bonus = 0.05 if '?' in text else 0.0

        # Exclamation points (but diminishing returns for multiple)
        exclaim_count = text.count('!')
        exclaim_bonus = min(exclaim_count * 0.02, 0.05)

        # Calculate final strength
        strength = max_score + ensemble_bonus + power_word_bonus + question_bonus + exclaim_bonus

        # Normalize to 0-1 range
        strength = min(max(strength, 0.0), 1.0)

        return strength

    def batch_classify(self, texts: List[str], batch_size: int = 32) -> List[HookClassification]:
        """
        Classify multiple hooks in batches for efficiency.

        Args:
            texts: List of hook texts
            batch_size: Batch size for processing

        Returns:
            List of HookClassification results
        """
        results = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            for text in batch:
                classification = self.classify(text)
                results.append(classification)

        return results

    def train(
        self,
        train_data: List[Dict[str, str]],
        val_data: Optional[List[Dict[str, str]]] = None,
        output_dir: Optional[str] = None,
        num_epochs: int = 3,
        learning_rate: float = 2e-5,
        batch_size: int = 16
    ) -> Dict[str, Any]:
        """
        Fine-tune the classifier on custom hook data.

        Args:
            train_data: List of {'text': hook_text, 'label': hook_type}
            val_data: Optional validation data in same format
            output_dir: Directory to save fine-tuned model
            num_epochs: Number of training epochs
            learning_rate: Learning rate for optimizer
            batch_size: Training batch size

        Returns:
            Training results and metrics
        """
        self._load_model()

        if output_dir is None:
            output_dir = str(Path(self.cache_dir) / "hook_classifier_finetuned")

        logger.info(f"Starting fine-tuning on {len(train_data)} examples")

        # Prepare datasets
        train_texts = [item['text'] for item in train_data]
        train_labels = [self.hook_to_label[item['label']] for item in train_data]

        train_dataset = HookDataset(train_texts, train_labels, self.tokenizer)

        val_dataset = None
        if val_data:
            val_texts = [item['text'] for item in val_data]
            val_labels = [self.hook_to_label[item['label']] for item in val_data]
            val_dataset = HookDataset(val_texts, val_labels, self.tokenizer)

        # Training arguments
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=num_epochs,
            per_device_train_batch_size=batch_size,
            per_device_eval_batch_size=batch_size,
            learning_rate=learning_rate,
            weight_decay=0.01,
            logging_dir=f"{output_dir}/logs",
            logging_steps=10,
            evaluation_strategy="epoch" if val_dataset else "no",
            save_strategy="epoch",
            load_best_model_at_end=True if val_dataset else False,
            warmup_steps=100,
            fp16=torch.cuda.is_available(),
        )

        # Data collator
        data_collator = DataCollatorWithPadding(tokenizer=self.tokenizer)

        # Trainer
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=val_dataset,
            data_collator=data_collator,
        )

        # Train
        logger.info("Training started...")
        train_result = trainer.train()

        # Save model
        trainer.save_model(output_dir)
        self.tokenizer.save_pretrained(output_dir)

        logger.info(f"✅ Model fine-tuned and saved to {output_dir}")

        # Evaluate
        metrics = {}
        if val_dataset:
            eval_result = trainer.evaluate()
            metrics['eval'] = eval_result

        metrics['train'] = train_result.metrics

        return {
            'success': True,
            'output_dir': output_dir,
            'metrics': metrics,
            'num_train_examples': len(train_data),
            'num_val_examples': len(val_data) if val_data else 0
        }

    def get_hook_examples(self) -> Dict[str, List[str]]:
        """
        Get example hooks for each type (useful for testing and documentation).

        Returns:
            Dictionary mapping hook types to example texts
        """
        return {
            'curiosity_gap': [
                "This one trick changed everything...",
                "You won't believe what happened next",
                "The secret nobody wants you to know",
                "I discovered something shocking about..."
            ],
            'transformation': [
                "From $0 to $10k in 30 days",
                "Before I was struggling, now I'm thriving",
                "Watch this complete transformation",
                "This is how I went from broke to profitable"
            ],
            'urgency_scarcity': [
                "Only 24 hours left to get this deal",
                "Limited spots available - act now",
                "This offer expires tonight",
                "Last chance before price doubles"
            ],
            'social_proof': [
                "Over 10,000 customers have already transformed their lives",
                "Client just hit $50k using this exact strategy",
                "Real results from real people",
                "My student made $5k in the first week"
            ],
            'pattern_interrupt': [
                "Stop what you're doing right now",
                "Everyone is doing this wrong",
                "Throw away everything you thought you knew",
                "This goes against everything they teach"
            ],
            'question': [
                "Are you making these costly mistakes?",
                "What if I told you there's a better way?",
                "How would your life change if...?",
                "Do you want to know the real secret?"
            ],
            'negative_hook': [
                "Stop wasting money on ads that don't work",
                "The 5 mistakes killing your business",
                "Never do this in your videos",
                "Avoid these fatal errors"
            ],
            'story_hook': [
                "Three months ago, I was living in my car...",
                "Let me tell you about the worst day of my life",
                "I'll never forget the moment I realized",
                "This started when I lost everything"
            ],
            'statistic_hook': [
                "95% of businesses fail because of this",
                "Studies show this increases conversions by 347%",
                "Only 3% of people know this strategy",
                "$10 million in revenue from one video"
            ],
            'controversy_hook': [
                "Everything you know about marketing is wrong",
                "The industry doesn't want you to know this",
                "This controversial method actually works",
                "Why the experts are lying to you"
            ]
        }

    def analyze_top_performer_hooks(self, hooks: List[str]) -> Dict[str, Any]:
        """
        Analyze multiple hooks from top-performing ads to identify patterns.

        Args:
            hooks: List of hook texts from top performers

        Returns:
            Aggregated analysis with dominant patterns
        """
        if not hooks:
            return {'error': 'No hooks provided'}

        # Classify all hooks
        classifications = self.batch_classify(hooks)

        # Aggregate statistics
        hook_type_counts = {hook_type: 0 for hook_type in self.HOOK_TYPES}
        total_confidence = 0.0
        total_strength = 0.0

        for classification in classifications:
            hook_type_counts[classification.primary_hook] += 1
            total_confidence += classification.confidence
            total_strength += classification.hook_strength

        # Calculate averages
        num_hooks = len(classifications)
        avg_confidence = total_confidence / num_hooks
        avg_strength = total_strength / num_hooks

        # Find dominant hook types
        sorted_types = sorted(
            hook_type_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Top 3 patterns
        top_patterns = [
            {
                'type': hook_type,
                'count': count,
                'percentage': (count / num_hooks) * 100
            }
            for hook_type, count in sorted_types[:3]
        ]

        return {
            'total_hooks_analyzed': num_hooks,
            'avg_confidence': avg_confidence,
            'avg_strength': avg_strength,
            'hook_type_distribution': hook_type_counts,
            'top_patterns': top_patterns,
            'dominant_pattern': sorted_types[0][0] if sorted_types else None,
            'recommendations': self._generate_pattern_recommendations(top_patterns, avg_strength)
        }

    def _generate_pattern_recommendations(
        self,
        top_patterns: List[Dict],
        avg_strength: float
    ) -> List[str]:
        """Generate recommendations based on pattern analysis"""
        recommendations = []

        if not top_patterns:
            return ["Not enough data to generate recommendations"]

        # Dominant pattern recommendation
        dominant = top_patterns[0]
        recommendations.append(
            f"✅ Your top-performing hook type is '{dominant['type']}' "
            f"({dominant['percentage']:.1f}% of top ads)"
        )

        # Strength analysis
        if avg_strength < 0.5:
            recommendations.append(
                "⚠️ Average hook strength is low - consider using more power words and emotional triggers"
            )
        elif avg_strength > 0.7:
            recommendations.append(
                "✅ Strong hook strength across top performers - your messaging is compelling"
            )

        # Diversity recommendation
        if dominant['percentage'] > 70:
            recommendations.append(
                "💡 Consider testing other hook types to diversify your creative approach"
            )
        elif dominant['percentage'] < 30:
            recommendations.append(
                "💡 Your hooks are diverse - focus on scaling the top 2-3 patterns"
            )

        return recommendations


# Singleton instance with lazy loading
_hook_classifier_instance = None

def get_hook_classifier() -> HookClassifier:
    """Get or create the global HookClassifier instance"""
    global _hook_classifier_instance
    if _hook_classifier_instance is None:
        _hook_classifier_instance = HookClassifier(lazy_load=True)
    return _hook_classifier_instance
