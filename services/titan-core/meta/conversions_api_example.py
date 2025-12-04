"""
Example usage of Meta Conversions API (CAPI).

This demonstrates how to use the MetaCAPI class for server-side event tracking.
"""

import os
from conversions_api import MetaCAPI, UserInfo
from facebook_business.adobjects.serverside.event import Event
from facebook_business.adobjects.serverside.user_data import UserData
from facebook_business.adobjects.serverside.custom_data import CustomData
from facebook_business.adobjects.serverside.action_source import ActionSource
import time


def example_basic_purchase():
    """Example: Track a purchase conversion."""
    # Initialize CAPI client
    capi = MetaCAPI(
        pixel_id=os.getenv('META_PIXEL_ID', 'YOUR_PIXEL_ID'),
        access_token=os.getenv('META_ACCESS_TOKEN', 'YOUR_ACCESS_TOKEN'),
        test_event_code=os.getenv('META_TEST_CODE')  # Optional: for testing
    )

    # Create user information
    user = UserInfo(
        email='john.doe@example.com',
        phone='+15551234567',
        first_name='John',
        last_name='Doe',
        city='San Francisco',
        state='CA',
        zip_code='94103',
        country='US',
        external_id='user_12345',
        client_ip_address='192.168.1.1',
        client_user_agent='Mozilla/5.0...',
        fbp='fb.1.1234567890123.1234567890',  # From _fbp cookie
        fbc='fb.1.1234567890123.AbCdEfGhIjKlMnOpQrStUvWxYz'  # From fbclid
    )

    # Send purchase event
    response = capi.send_purchase_event(
        user=user,
        value=99.99,
        currency='USD',
        content_ids=['product_123', 'product_456'],
        content_type='product',
        order_id='order_789',
        event_id='unique_event_id_123'  # For deduplication with pixel
    )

    print('Purchase event response:', response)


def example_lead_generation():
    """Example: Track lead form submission."""
    capi = MetaCAPI(
        pixel_id=os.getenv('META_PIXEL_ID'),
        access_token=os.getenv('META_ACCESS_TOKEN'),
        test_event_code=os.getenv('META_TEST_CODE')
    )

    user = UserInfo(
        email='jane.smith@example.com',
        first_name='Jane',
        last_name='Smith',
        client_ip_address='192.168.1.2',
        client_user_agent='Mozilla/5.0...'
    )

    response = capi.send_lead_event(
        user=user,
        lead_id='lead_456',
        content_name='Newsletter Signup',
        event_id=capi.generate_event_id()
    )

    print('Lead event response:', response)


def example_ecommerce_funnel():
    """Example: Track complete e-commerce funnel."""
    capi = MetaCAPI(
        pixel_id=os.getenv('META_PIXEL_ID'),
        access_token=os.getenv('META_ACCESS_TOKEN')
    )

    user = UserInfo(
        email='customer@example.com',
        external_id='customer_999',
        client_ip_address='192.168.1.3',
        fbp='fb.1.1234567890123.9876543210'
    )

    # Step 1: View content
    print('1. Tracking ViewContent...')
    capi.send_view_content_event(
        user=user,
        content_id='product_789',
        content_name='Premium Video Course',
        content_category='Education',
        value=299.00,
        currency='USD'
    )

    # Step 2: Add to cart
    print('2. Tracking AddToCart...')
    capi.send_add_to_cart_event(
        user=user,
        content_id='product_789',
        value=299.00,
        currency='USD'
    )

    # Step 3: Initiate checkout
    print('3. Tracking InitiateCheckout...')
    capi.send_initiate_checkout_event(
        user=user,
        content_ids=['product_789'],
        value=299.00,
        currency='USD',
        num_items=1
    )

    # Step 4: Complete purchase
    print('4. Tracking Purchase...')
    response = capi.send_purchase_event(
        user=user,
        value=299.00,
        currency='USD',
        content_ids=['product_789'],
        order_id='order_final_123'
    )

    print('Funnel tracking complete:', response)


def example_batch_events():
    """Example: Send multiple events in batch."""
    capi = MetaCAPI(
        pixel_id=os.getenv('META_PIXEL_ID'),
        access_token=os.getenv('META_ACCESS_TOKEN')
    )

    # Create multiple events
    events = []

    # Event 1: User A views content
    user_a = capi._build_user_data(UserInfo(
        email='usera@example.com',
        client_ip_address='192.168.1.10'
    ))

    event1 = Event(
        event_name='ViewContent',
        event_time=int(time.time()),
        user_data=user_a,
        custom_data=CustomData(
            content_ids=['product_100'],
            content_type='product',
            value=49.99,
            currency='USD'
        ),
        action_source=ActionSource.WEBSITE,
        event_id=capi.generate_event_id()
    )
    events.append(event1)

    # Event 2: User B completes registration
    user_b = capi._build_user_data(UserInfo(
        email='userb@example.com',
        first_name='Bob',
        last_name='Johnson',
        client_ip_address='192.168.1.11'
    ))

    event2 = Event(
        event_name='CompleteRegistration',
        event_time=int(time.time()),
        user_data=user_b,
        custom_data=CustomData(
            content_name='Free Trial Signup',
            status='complete'
        ),
        action_source=ActionSource.WEBSITE,
        event_id=capi.generate_event_id()
    )
    events.append(event2)

    # Send batch
    response = capi.batch_events(events)
    print(f'Batch events response (sent {len(events)} events):', response)


def example_custom_event():
    """Example: Send custom event."""
    capi = MetaCAPI(
        pixel_id=os.getenv('META_PIXEL_ID'),
        access_token=os.getenv('META_ACCESS_TOKEN')
    )

    user = UserInfo(
        email='custom@example.com',
        client_ip_address='192.168.1.20'
    )

    response = capi.send_custom_event(
        user=user,
        event_name='VideoWatched',
        custom_data={
            'video_id': 'video_123',
            'video_title': 'Product Demo',
            'watch_time': 120,
            'completion_rate': 0.75
        }
    )

    print('Custom event response:', response)


def example_deduplication():
    """Example: Event deduplication with pixel."""
    capi = MetaCAPI(
        pixel_id=os.getenv('META_PIXEL_ID'),
        access_token=os.getenv('META_ACCESS_TOKEN')
    )

    # Generate event ID that will be shared between pixel and CAPI
    event_id = capi.generate_event_id()
    print(f'Generated event_id for deduplication: {event_id}')

    # This event_id should be:
    # 1. Sent via pixel (browser-side): fbq('track', 'Purchase', {...}, {eventID: '{event_id}'})
    # 2. Sent via CAPI (server-side) with the same event_id
    # Meta will automatically deduplicate based on matching event_id

    user = UserInfo(
        email='dedup@example.com',
        external_id='user_dedup_123',
        client_ip_address='192.168.1.30',
        fbp='fb.1.1234567890123.1111111111'
    )

    response = capi.send_purchase_event(
        user=user,
        value=149.99,
        currency='USD',
        content_ids=['product_dedup'],
        event_id=event_id  # Same ID used in pixel
    )

    # Validate event ID
    is_valid = capi.deduplicate_with_pixel(event_id)
    print(f'Event ID valid for deduplication: {is_valid}')
    print('Purchase with deduplication response:', response)


def example_registration_flow():
    """Example: Complete user registration flow."""
    capi = MetaCAPI(
        pixel_id=os.getenv('META_PIXEL_ID'),
        access_token=os.getenv('META_ACCESS_TOKEN')
    )

    user = UserInfo(
        email='newuser@example.com',
        phone='+15559876543',
        first_name='Alice',
        last_name='Williams',
        city='New York',
        state='NY',
        country='US',
        client_ip_address='192.168.1.40',
        client_user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    )

    response = capi.send_complete_registration_event(
        user=user,
        content_name='Free Account Creation',
        status='complete'
    )

    print('Registration event response:', response)


if __name__ == '__main__':
    print('=== Meta Conversions API Examples ===\n')

    # Note: Set environment variables before running:
    # export META_PIXEL_ID='your_pixel_id'
    # export META_ACCESS_TOKEN='your_access_token'
    # export META_TEST_CODE='your_test_code'  # Optional

    print('Example 1: Basic Purchase Event')
    print('-' * 50)
    # example_basic_purchase()

    print('\nExample 2: Lead Generation')
    print('-' * 50)
    # example_lead_generation()

    print('\nExample 3: E-commerce Funnel')
    print('-' * 50)
    # example_ecommerce_funnel()

    print('\nExample 4: Batch Events')
    print('-' * 50)
    # example_batch_events()

    print('\nExample 5: Custom Event')
    print('-' * 50)
    # example_custom_event()

    print('\nExample 6: Event Deduplication')
    print('-' * 50)
    # example_deduplication()

    print('\nExample 7: Registration Flow')
    print('-' * 50)
    # example_registration_flow()

    print('\n' + '=' * 50)
    print('Uncomment the examples you want to run.')
    print('Make sure to set your Meta credentials first!')
