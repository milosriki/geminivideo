"""
Unit tests for HookClassifier
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Mock transformers if not available for testing
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class TestHookClassifier(unittest.TestCase):
    """Test cases for HookClassifier"""

    def setUp(self):
        """Set up test fixtures"""
        if not TRANSFORMERS_AVAILABLE:
            self.skipTest("transformers not available")

        from hook_classifier import HookClassifier
        self.classifier_class = HookClassifier

    def test_hook_types_count(self):
        """Test that we have exactly 10 hook types"""
        self.assertEqual(len(self.classifier_class.HOOK_TYPES), 10)

    def test_hook_types_content(self):
        """Test that all expected hook types are present"""
        expected_types = {
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
        }
        self.assertEqual(set(self.classifier_class.HOOK_TYPES), expected_types)

    def test_lazy_loading(self):
        """Test that lazy loading works"""
        classifier = self.classifier_class(lazy_load=True)
        self.assertFalse(classifier._model_loaded)
        self.assertIsNone(classifier.model)
        self.assertIsNone(classifier.tokenizer)

    def test_device_auto_detection(self):
        """Test device auto-detection"""
        classifier = self.classifier_class(lazy_load=True)
        self.assertIn(classifier.device, ['cpu', 'cuda', 'mps'])

    def test_label_mappings(self):
        """Test label to hook and hook to label mappings"""
        classifier = self.classifier_class(lazy_load=True)

        # Check bidirectional mapping
        for i, hook in enumerate(self.classifier_class.HOOK_TYPES):
            self.assertEqual(classifier.label_to_hook[i], hook)
            self.assertEqual(classifier.hook_to_label[hook], i)

    def test_get_hook_examples(self):
        """Test that get_hook_examples returns examples for all types"""
        classifier = self.classifier_class(lazy_load=True)
        examples = classifier.get_hook_examples()

        # Should have examples for all 10 types
        self.assertEqual(len(examples), 10)

        # Each type should have multiple examples
        for hook_type in self.classifier_class.HOOK_TYPES:
            self.assertIn(hook_type, examples)
            self.assertIsInstance(examples[hook_type], list)
            self.assertGreater(len(examples[hook_type]), 0)

    @patch('hook_classifier.AutoTokenizer')
    @patch('hook_classifier.AutoModelForSequenceClassification')
    def test_model_loading(self, mock_model, mock_tokenizer):
        """Test model loading mechanism"""
        # Setup mocks
        mock_tokenizer.from_pretrained.return_value = Mock()
        mock_model_instance = Mock()
        mock_model_instance.to.return_value = mock_model_instance
        mock_model_instance.eval.return_value = mock_model_instance
        mock_model.from_pretrained.return_value = mock_model_instance

        # Create classifier with lazy loading disabled
        classifier = self.classifier_class(lazy_load=False)

        # Verify model was loaded
        self.assertTrue(classifier._model_loaded)
        mock_tokenizer.from_pretrained.assert_called_once()
        mock_model.from_pretrained.assert_called_once()

    def test_calculate_hook_strength_power_words(self):
        """Test hook strength calculation with power words"""
        classifier = self.classifier_class(lazy_load=True)

        scores = {hook: 0.5 for hook in self.classifier_class.HOOK_TYPES}

        # Text with power words
        text_with_power = "secret proven guaranteed discover shocking"
        strength = classifier._calculate_hook_strength(text_with_power, scores)

        # Text without power words
        text_without = "this is a normal sentence"
        strength_normal = classifier._calculate_hook_strength(text_without, scores)

        # Power words should increase strength
        self.assertGreater(strength, strength_normal)

    def test_calculate_hook_strength_questions(self):
        """Test hook strength calculation with questions"""
        classifier = self.classifier_class(lazy_load=True)

        scores = {hook: 0.5 for hook in self.classifier_class.HOOK_TYPES}

        # Text with question
        text_with_question = "Are you making these mistakes?"
        strength_q = classifier._calculate_hook_strength(text_with_question, scores)

        # Text without question
        text_without = "You are making these mistakes"
        strength_no_q = classifier._calculate_hook_strength(text_without, scores)

        # Question should increase strength
        self.assertGreater(strength_q, strength_no_q)

    def test_calculate_hook_strength_exclamations(self):
        """Test hook strength calculation with exclamations"""
        classifier = self.classifier_class(lazy_load=True)

        scores = {hook: 0.5 for hook in self.classifier_class.HOOK_TYPES}

        # Text with exclamation
        text_with_exclaim = "Stop right now!"
        strength_e = classifier._calculate_hook_strength(text_with_exclaim, scores)

        # Text without
        text_without = "Stop right now"
        strength_no_e = classifier._calculate_hook_strength(text_without, scores)

        # Exclamation should increase strength
        self.assertGreater(strength_e, strength_no_e)

    def test_calculate_hook_strength_range(self):
        """Test that hook strength is always in 0-1 range"""
        classifier = self.classifier_class(lazy_load=True)

        # Test with extreme scores
        extreme_scores = {hook: 1.0 for hook in self.classifier_class.HOOK_TYPES}
        extreme_text = "secret! proven! guaranteed! shocking! discover! ?"

        strength = classifier._calculate_hook_strength(extreme_text, extreme_scores)

        # Should be clamped to 1.0
        self.assertLessEqual(strength, 1.0)
        self.assertGreaterEqual(strength, 0.0)

    def test_pattern_recommendations_low_strength(self):
        """Test recommendations for low hook strength"""
        classifier = self.classifier_class(lazy_load=True)

        top_patterns = [
            {'type': 'transformation', 'count': 5, 'percentage': 50.0}
        ]

        recommendations = classifier._generate_pattern_recommendations(
            top_patterns,
            avg_strength=0.3  # Low strength
        )

        # Should include low strength warning
        self.assertTrue(any('low' in rec.lower() for rec in recommendations))

    def test_pattern_recommendations_high_strength(self):
        """Test recommendations for high hook strength"""
        classifier = self.classifier_class(lazy_load=True)

        top_patterns = [
            {'type': 'transformation', 'count': 5, 'percentage': 50.0}
        ]

        recommendations = classifier._generate_pattern_recommendations(
            top_patterns,
            avg_strength=0.8  # High strength
        )

        # Should include positive feedback
        self.assertTrue(any('strong' in rec.lower() for rec in recommendations))

    def test_pattern_recommendations_diversity(self):
        """Test recommendations for hook diversity"""
        classifier = self.classifier_class(lazy_load=True)

        # High concentration
        high_concentration = [
            {'type': 'transformation', 'count': 8, 'percentage': 80.0}
        ]
        recs_concentrated = classifier._generate_pattern_recommendations(
            high_concentration, 0.6
        )

        # Should suggest testing other types
        self.assertTrue(any('diversify' in rec.lower() or 'other' in rec.lower()
                          for rec in recs_concentrated))

        # Low concentration (diverse)
        diverse = [
            {'type': 'transformation', 'count': 2, 'percentage': 20.0}
        ]
        recs_diverse = classifier._generate_pattern_recommendations(diverse, 0.6)

        # Should suggest focusing
        self.assertTrue(any('focus' in rec.lower() or 'scale' in rec.lower()
                          for rec in recs_diverse))


class TestHookClassifierIntegration(unittest.TestCase):
    """Integration tests (require transformers)"""

    def setUp(self):
        """Set up test fixtures"""
        if not TRANSFORMERS_AVAILABLE:
            self.skipTest("transformers not available")

        from hook_classifier import get_hook_classifier
        self.get_classifier = get_hook_classifier

    def test_singleton_pattern(self):
        """Test that get_hook_classifier returns same instance"""
        classifier1 = self.get_classifier()
        classifier2 = self.get_classifier()
        self.assertIs(classifier1, classifier2)


class TestMetaLearningAgentIntegration(unittest.TestCase):
    """Test integration with Meta Learning Agent"""

    def test_import_in_meta_agent(self):
        """Test that meta_learning_agent can import hook classifier"""
        try:
            import sys
            import os
            # Add parent directory to path
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

            from meta_learning_agent import MetaLearningAgent, HOOK_CLASSIFIER_AVAILABLE

            # Should import without errors
            self.assertIsNotNone(MetaLearningAgent)

            # If transformers available, flag should be True
            if TRANSFORMERS_AVAILABLE:
                self.assertTrue(HOOK_CLASSIFIER_AVAILABLE)

        except ImportError as e:
            self.skipTest(f"Could not import meta_learning_agent: {e}")

    def test_fallback_keyword_analysis(self):
        """Test that fallback keyword analysis works"""
        try:
            import sys
            import os
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

            from meta_learning_agent import MetaLearningAgent

            agent = MetaLearningAgent()

            # Test fallback analysis
            test_performers = [
                {
                    'ad_name': 'Stop wasting money on ads',
                    'campaign_name': 'Test Campaign'
                },
                {
                    'ad_name': 'From $0 to $10k transformation',
                    'campaign_name': 'Results Campaign'
                }
            ]

            result = agent._fallback_keyword_analysis(test_performers)

            # Should return dictionary with hook types
            self.assertIsInstance(result, dict)
            self.assertIn('transformation', result)
            self.assertIn('negative_hook', result)
            self.assertIn('_ml_analysis', result)

            # Should detect transformation and negative hooks
            self.assertGreater(result['transformation'], 0)
            self.assertGreater(result['negative_hook'], 0)

        except ImportError as e:
            self.skipTest(f"Could not import meta_learning_agent: {e}")


def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test cases
    suite.addTests(loader.loadTestsFromTestCase(TestHookClassifier))
    suite.addTests(loader.loadTestsFromTestCase(TestHookClassifierIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestMetaLearningAgentIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)
