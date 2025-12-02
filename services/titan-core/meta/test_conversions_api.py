"""
Unit tests for Meta Conversions API (CAPI).

Tests the MetaCAPI implementation without making real API calls.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import hashlib
from conversions_api import MetaCAPI, UserInfo
from facebook_business.adobjects.serverside.event import Event
from facebook_business.adobjects.serverside.user_data import UserData


class TestMetaCAPI(unittest.TestCase):
    """Test cases for MetaCAPI class."""

    def setUp(self):
        """Set up test fixtures."""
        self.pixel_id = 'test_pixel_12345'
        self.access_token = 'test_token_abc123'
        self.test_code = 'TEST12345'

    @patch('conversions_api.FacebookAdsApi.init')
    def test_initialization(self, mock_init):
        """Test CAPI client initialization."""
        capi = MetaCAPI(
            pixel_id=self.pixel_id,
            access_token=self.access_token,
            test_event_code=self.test_code
        )

        self.assertEqual(capi.pixel_id, self.pixel_id)
        self.assertEqual(capi.access_token, self.access_token)
        self.assertEqual(capi.test_event_code, self.test_code)
        mock_init.assert_called_once_with(access_token=self.access_token)

    @patch('conversions_api.FacebookAdsApi.init')
    def test_hash_pii(self, mock_init):
        """Test PII hashing with SHA256."""
        capi = MetaCAPI(self.pixel_id, self.access_token)

        # Test email hashing
        email = 'Test@Example.com'
        hashed = capi._hash_pii(email)

        # Expected: lowercase, trimmed, then SHA256
        expected = hashlib.sha256('test@example.com'.encode('utf-8')).hexdigest()
        self.assertEqual(hashed, expected)

        # Test with whitespace
        name = '  John Doe  '
        hashed_name = capi._hash_pii(name)
        expected_name = hashlib.sha256('john doe'.encode('utf-8')).hexdigest()
        self.assertEqual(hashed_name, expected_name)

        # Test None value
        self.assertIsNone(capi._hash_pii(None))
        self.assertIsNone(capi._hash_pii(''))

    @patch('conversions_api.FacebookAdsApi.init')
    def test_build_user_data(self, mock_init):
        """Test UserData object construction."""
        capi = MetaCAPI(self.pixel_id, self.access_token)

        user = UserInfo(
            email='test@example.com',
            phone='+15551234567',
            first_name='John',
            last_name='Doe',
            city='San Francisco',
            state='CA',
            zip_code='94103',
            country='US',
            external_id='user_123',
            client_ip_address='192.168.1.1',
            client_user_agent='Mozilla/5.0...',
            fbp='fb.1.123.456',
            fbc='fb.1.123.abc'
        )

        user_data = capi._build_user_data(user)

        # Verify PII fields are hashed
        self.assertEqual(user_data.email, capi._hash_pii('test@example.com'))
        self.assertEqual(user_data.phone, capi._hash_pii('+15551234567'))
        self.assertEqual(user_data.first_name, capi._hash_pii('John'))
        self.assertEqual(user_data.last_name, capi._hash_pii('Doe'))

        # Verify non-PII fields are not hashed
        self.assertEqual(user_data.client_ip_address, '192.168.1.1')
        self.assertEqual(user_data.client_user_agent, 'Mozilla/5.0...')
        self.assertEqual(user_data.fbp, 'fb.1.123.456')
        self.assertEqual(user_data.fbc, 'fb.1.123.abc')

    @patch('conversions_api.FacebookAdsApi.init')
    @patch('conversions_api.EventRequest')
    def test_send_purchase_event(self, mock_event_request, mock_init):
        """Test sending purchase event."""
        capi = MetaCAPI(self.pixel_id, self.access_token)

        # Mock API response
        mock_response = Mock()
        mock_response.events_received = 1
        mock_response.messages = []
        mock_response.fbtrace_id = 'trace_123'
        mock_event_request.return_value.execute.return_value = mock_response

        user = UserInfo(
            email='customer@example.com',
            external_id='user_999'
        )

        response = capi.send_purchase_event(
            user=user,
            value=99.99,
            currency='USD',
            content_ids=['product_123'],
            order_id='order_456',
            event_id='event_789'
        )

        self.assertTrue(response['success'])
        self.assertEqual(response['events_received'], 1)
        self.assertEqual(response['fbtrace_id'], 'trace_123')

    @patch('conversions_api.FacebookAdsApi.init')
    @patch('conversions_api.EventRequest')
    def test_send_lead_event(self, mock_event_request, mock_init):
        """Test sending lead event."""
        capi = MetaCAPI(self.pixel_id, self.access_token)

        mock_response = Mock()
        mock_response.events_received = 1
        mock_response.messages = []
        mock_response.fbtrace_id = 'trace_456'
        mock_event_request.return_value.execute.return_value = mock_response

        user = UserInfo(email='lead@example.com')

        response = capi.send_lead_event(
            user=user,
            lead_id='lead_123',
            content_name='Newsletter Signup'
        )

        self.assertTrue(response['success'])

    @patch('conversions_api.FacebookAdsApi.init')
    @patch('conversions_api.EventRequest')
    def test_batch_events(self, mock_event_request, mock_init):
        """Test batch event sending."""
        capi = MetaCAPI(self.pixel_id, self.access_token)

        mock_response = Mock()
        mock_response.events_received = 2
        mock_response.messages = []
        mock_response.fbtrace_id = 'trace_batch'
        mock_event_request.return_value.execute.return_value = mock_response

        # Create mock events
        events = [Mock(spec=Event), Mock(spec=Event)]

        response = capi.batch_events(events)

        self.assertTrue(response['success'])
        self.assertEqual(response['events_received'], 2)

    @patch('conversions_api.FacebookAdsApi.init')
    def test_batch_events_limit(self, mock_init):
        """Test batch events enforces 1000 event limit."""
        capi = MetaCAPI(self.pixel_id, self.access_token)

        # Create 1001 events
        events = [Mock(spec=Event) for _ in range(1001)]

        with self.assertRaises(ValueError) as context:
            capi.batch_events(events)

        self.assertIn('Maximum 1000 events', str(context.exception))

    @patch('conversions_api.FacebookAdsApi.init')
    def test_generate_event_id(self, mock_init):
        """Test event ID generation."""
        capi = MetaCAPI(self.pixel_id, self.access_token)

        event_id1 = capi.generate_event_id()
        event_id2 = capi.generate_event_id()

        # Should be different UUIDs
        self.assertNotEqual(event_id1, event_id2)

        # Should be valid UUID format
        import uuid
        uuid.UUID(event_id1)  # Will raise if invalid
        uuid.UUID(event_id2)

    @patch('conversions_api.FacebookAdsApi.init')
    def test_deduplicate_with_pixel(self, mock_init):
        """Test event ID validation for deduplication."""
        capi = MetaCAPI(self.pixel_id, self.access_token)

        # Valid UUID
        valid_id = capi.generate_event_id()
        self.assertTrue(capi.deduplicate_with_pixel(valid_id))

        # Invalid UUID
        self.assertFalse(capi.deduplicate_with_pixel('invalid_id'))
        self.assertFalse(capi.deduplicate_with_pixel(''))
        self.assertFalse(capi.deduplicate_with_pixel(None))

    @patch('conversions_api.FacebookAdsApi.init')
    @patch('conversions_api.EventRequest')
    def test_send_view_content_event(self, mock_event_request, mock_init):
        """Test sending view content event."""
        capi = MetaCAPI(self.pixel_id, self.access_token)

        mock_response = Mock()
        mock_response.events_received = 1
        mock_response.messages = []
        mock_response.fbtrace_id = 'trace_view'
        mock_event_request.return_value.execute.return_value = mock_response

        user = UserInfo(email='viewer@example.com')

        response = capi.send_view_content_event(
            user=user,
            content_id='product_789',
            content_name='Premium Course',
            value=299.00
        )

        self.assertTrue(response['success'])

    @patch('conversions_api.FacebookAdsApi.init')
    @patch('conversions_api.EventRequest')
    def test_send_custom_event(self, mock_event_request, mock_init):
        """Test sending custom event."""
        capi = MetaCAPI(self.pixel_id, self.access_token)

        mock_response = Mock()
        mock_response.events_received = 1
        mock_response.messages = []
        mock_response.fbtrace_id = 'trace_custom'
        mock_event_request.return_value.execute.return_value = mock_response

        user = UserInfo(email='custom@example.com')

        response = capi.send_custom_event(
            user=user,
            event_name='VideoWatched',
            custom_data={'video_id': 'vid_123', 'duration': 120}
        )

        self.assertTrue(response['success'])

    @patch('conversions_api.FacebookAdsApi.init')
    @patch('conversions_api.EventRequest')
    def test_error_handling(self, mock_event_request, mock_init):
        """Test error handling in event sending."""
        capi = MetaCAPI(self.pixel_id, self.access_token)

        # Mock API error
        mock_event_request.return_value.execute.side_effect = Exception('API Error')

        user = UserInfo(email='error@example.com')

        with self.assertRaises(Exception) as context:
            capi.send_purchase_event(user=user, value=100.0)

        self.assertIn('API Error', str(context.exception))


if __name__ == '__main__':
    unittest.main()
