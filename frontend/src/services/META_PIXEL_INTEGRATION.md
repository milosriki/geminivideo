# Meta Pixel Integration Guide

This guide explains how to integrate Meta Pixel tracking into your application using the `metaPixel` service and `useMetaPixel` hook.

## Quick Start

### 1. Configure Environment Variable

Add your Meta Pixel ID to `.env`:

```bash
VITE_META_PIXEL_ID=your_pixel_id_here
```

Get your Pixel ID from [Meta Events Manager](https://business.facebook.com/events_manager).

### 2. Initialize Pixel

Initialize the pixel in your root App component:

```typescript
import { metaPixel } from './services/metaPixel';

function App() {
  useEffect(() => {
    metaPixel.initPixel();
  }, []);

  return <YourAppContent />;
}
```

### 3. Use the Hook in Components (Recommended)

```typescript
import { useMetaPixel } from './hooks/useMetaPixel';

function ProductPage({ product }) {
  const pixel = useMetaPixel({
    autoTrackPageView: true,
    trackRouteChanges: true,
    debug: false
  });

  // Track product view
  useEffect(() => {
    pixel.trackViewContent({
      contentId: product.id,
      contentName: product.name,
      value: product.price,
      currency: 'USD',
      autoGenerateEventId: true
    });
  }, [product]);

  // Track add to cart
  const handleAddToCart = () => {
    pixel.trackAddToCart({
      contentId: product.id,
      value: product.price,
      currency: 'USD',
      autoGenerateEventId: true
    });
  };

  return <button onClick={handleAddToCart}>Add to Cart</button>;
}
```

## Standard Events

### PageView
Automatically tracked when using `useMetaPixel` hook with `autoTrackPageView: true`.

```typescript
pixel.trackPageView();
```

### ViewContent
Track when users view content (products, articles, etc.):

```typescript
pixel.trackViewContent({
  contentId: 'product-123',
  contentName: 'Product Name',
  value: 29.99,
  currency: 'USD',
  autoGenerateEventId: true
});
```

### Search
Track search queries:

```typescript
pixel.trackSearch({
  searchString: 'video editing',
  autoGenerateEventId: true
});
```

### AddToCart
Track add to cart events:

```typescript
pixel.trackAddToCart({
  contentId: 'product-123',
  value: 29.99,
  currency: 'USD',
  autoGenerateEventId: true
});
```

### AddToWishlist
Track wishlist additions:

```typescript
pixel.trackAddToWishlist({
  contentId: 'product-123',
  value: 29.99,
  currency: 'USD',
  autoGenerateEventId: true
});
```

### InitiateCheckout
Track checkout initiation:

```typescript
pixel.trackInitiateCheckout({
  contentIds: ['product-123', 'product-456'],
  value: 59.98,
  currency: 'USD',
  numItems: 2,
  autoGenerateEventId: true
});
```

### AddPaymentInfo
Track payment info addition:

```typescript
pixel.trackAddPaymentInfo({
  contentIds: cart.items.map(i => i.id),
  value: cart.total,
  currency: 'USD',
  autoGenerateEventId: true
});
```

### Purchase
Track completed purchases:

```typescript
pixel.trackPurchase({
  value: 59.98,
  currency: 'USD',
  content_ids: ['product-123', 'product-456'],
  contents: [
    { id: 'product-123', quantity: 1, item_price: 29.99 },
    { id: 'product-456', quantity: 1, item_price: 29.99 }
  ],
  num_items: 2,
  autoGenerateEventId: true
});
```

### Lead
Track lead generation:

```typescript
pixel.trackLead({
  contentName: 'Contact Form',
  autoGenerateEventId: true
});
```

### CompleteRegistration
Track user registrations:

```typescript
pixel.trackCompleteRegistration({
  contentName: 'User Account',
  status: 'completed',
  autoGenerateEventId: true
});
```

### Subscribe
Track subscriptions:

```typescript
pixel.trackSubscribe({
  value: 9.99,
  currency: 'USD',
  predictedLtv: 119.88, // Annual value
  autoGenerateEventId: true
});
```

## Custom Events

Track custom application-specific events:

```typescript
pixel.trackCustomEvent('VideoExported', {
  video_id: 'vid-123',
  video_duration: 120,
  export_quality: 'HD'
}, true); // autoGenerateEventId
```

## Advanced Matching

Set user data for improved ad targeting (automatically hashed client-side):

```typescript
await pixel.setAdvancedMatching({
  email: 'user@example.com',
  phone: '+15551234567',
  firstName: 'John',
  lastName: 'Doe',
  city: 'San Francisco',
  state: 'CA',
  zipCode: '94102',
  country: 'US',
  externalId: 'user-123'
});
```

Call this after user login/registration. All PII is hashed using SHA256 client-side.

## Event ID Deduplication

Event IDs are automatically generated to enable deduplication with Conversions API (CAPI):

```typescript
// Automatic generation (recommended)
pixel.trackPurchase({
  value: 100,
  currency: 'USD',
  autoGenerateEventId: true
});

// Manual generation
const eventId = pixel.generateEventId();
pixel.trackPurchase({
  value: 100,
  currency: 'USD',
  eventId: eventId
});

// Send same eventId to your backend for CAPI
await fetch('/api/track-purchase', {
  method: 'POST',
  body: JSON.stringify({ eventId, purchaseData })
});
```

## Debug Mode

Enable debug mode during development:

```typescript
const pixel = useMetaPixel({
  debug: process.env.NODE_ENV === 'development'
});

// Or directly
metaPixel.enableDebugMode();
```

Debug mode logs all tracking calls to the console.

## Complete E-commerce Flow Example

```typescript
function CheckoutFlow() {
  const pixel = useMetaPixel();
  const [cart, setCart] = useState([]);

  // Step 1: View product
  const viewProduct = (product) => {
    pixel.trackViewContent({
      contentId: product.id,
      value: product.price,
      currency: 'USD',
      autoGenerateEventId: true
    });
  };

  // Step 2: Add to cart
  const addToCart = (product) => {
    pixel.trackAddToCart({
      contentId: product.id,
      value: product.price,
      currency: 'USD',
      autoGenerateEventId: true
    });
    setCart([...cart, product]);
  };

  // Step 3: Initiate checkout
  const startCheckout = () => {
    pixel.trackInitiateCheckout({
      contentIds: cart.map(p => p.id),
      value: cart.reduce((sum, p) => sum + p.price, 0),
      currency: 'USD',
      numItems: cart.length,
      autoGenerateEventId: true
    });
  };

  // Step 4: Add payment info
  const addPayment = () => {
    pixel.trackAddPaymentInfo({
      contentIds: cart.map(p => p.id),
      value: cart.reduce((sum, p) => sum + p.price, 0),
      currency: 'USD',
      autoGenerateEventId: true
    });
  };

  // Step 5: Complete purchase
  const completePurchase = (orderId) => {
    const total = cart.reduce((sum, p) => sum + p.price, 0);

    pixel.trackPurchase({
      value: total,
      currency: 'USD',
      content_ids: cart.map(p => p.id),
      contents: cart.map(p => ({
        id: p.id,
        quantity: 1,
        item_price: p.price
      })),
      num_items: cart.length,
      autoGenerateEventId: true
    });
  };

  return <CheckoutComponent />;
}
```

## Privacy & Compliance

**Important**: Before implementing Meta Pixel tracking:

1. Update your privacy policy to disclose Meta Pixel usage
2. Implement cookie consent banner
3. Obtain user consent before tracking (GDPR, CCPA compliance)
4. Allow users to opt-out of tracking
5. Follow all applicable privacy regulations

## Testing

1. Install [Meta Pixel Helper](https://chrome.google.com/webstore/detail/meta-pixel-helper/) Chrome extension
2. Enable debug mode in development
3. Verify events in [Meta Events Manager](https://business.facebook.com/events_manager)
4. Test event deduplication with CAPI

## API Reference

See TypeScript definitions in:
- `/frontend/src/services/metaPixel.ts` - Service implementation
- `/frontend/src/hooks/useMetaPixel.ts` - React hook

## Support

For Meta Pixel documentation: https://developers.facebook.com/docs/meta-pixel
For Conversions API: https://developers.facebook.com/docs/marketing-api/conversions-api
