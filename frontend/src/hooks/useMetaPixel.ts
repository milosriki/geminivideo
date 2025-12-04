/**
 * React Hook for Meta Pixel Integration
 * Provides easy-to-use pixel tracking methods in React components
 *
 * Features:
 * - Automatic event ID generation
 * - Automatic page view tracking on route changes
 * - Type-safe pixel methods
 * - React lifecycle integration
 */

import { useEffect, useCallback, useRef } from 'react';
import { metaPixel, UserData, ContentInfo, PurchaseData } from '../services/metaPixel';

interface UseMetaPixelOptions {
  /**
   * Automatically track page views on component mount
   * @default true
   */
  autoTrackPageView?: boolean;

  /**
   * Enable debug mode
   * @default false
   */
  debug?: boolean;

  /**
   * Track page views on URL changes (for SPAs)
   * @default true
   */
  trackRouteChanges?: boolean;
}

interface MetaPixelMethods {
  // Core methods
  trackPageView: () => void;
  generateEventId: () => string;
  setAdvancedMatching: (userData: UserData) => Promise<void>;

  // Standard events
  trackViewContent: (params: {
    contentId: string;
    contentName?: string;
    contentCategory?: string;
    value?: number;
    currency?: string;
    autoGenerateEventId?: boolean;
  }) => void;

  trackSearch: (params: {
    searchString: string;
    contentIds?: string[];
    contentCategory?: string;
    autoGenerateEventId?: boolean;
  }) => void;

  trackAddToCart: (params: {
    contentId: string;
    contentName?: string;
    value: number;
    currency: string;
    autoGenerateEventId?: boolean;
  }) => void;

  trackAddToWishlist: (params: {
    contentId: string;
    contentName?: string;
    value?: number;
    currency?: string;
    autoGenerateEventId?: boolean;
  }) => void;

  trackInitiateCheckout: (params: {
    contentIds: string[];
    value: number;
    currency: string;
    numItems: number;
    autoGenerateEventId?: boolean;
  }) => void;

  trackAddPaymentInfo: (params: {
    contentIds?: string[];
    value?: number;
    currency?: string;
    autoGenerateEventId?: boolean;
  }) => void;

  trackPurchase: (params: PurchaseData & {
    autoGenerateEventId?: boolean;
  }) => void;

  trackLead: (params: {
    contentName?: string;
    contentCategory?: string;
    value?: number;
    currency?: string;
    autoGenerateEventId?: boolean;
  }) => void;

  trackCompleteRegistration: (params: {
    contentName?: string;
    status?: string;
    value?: number;
    currency?: string;
    autoGenerateEventId?: boolean;
  }) => void;

  trackSubscribe: (params: {
    value: number;
    currency: string;
    predictedLtv?: number;
    autoGenerateEventId?: boolean;
  }) => void;

  // Custom events
  trackCustomEvent: (
    eventName: string,
    params?: Record<string, any>,
    autoGenerateEventId?: boolean
  ) => void;

  // Utility
  isInitialized: () => boolean;
  getPixelId: () => string;
}

/**
 * Hook for Meta Pixel tracking in React components
 *
 * @example
 * ```tsx
 * function ProductPage({ productId }) {
 *   const pixel = useMetaPixel({ autoTrackPageView: true });
 *
 *   useEffect(() => {
 *     pixel.trackViewContent({
 *       contentId: productId,
 *       contentName: 'Product Name',
 *       value: 29.99,
 *       currency: 'USD',
 *       autoGenerateEventId: true
 *     });
 *   }, [productId]);
 *
 *   const handleAddToCart = () => {
 *     pixel.trackAddToCart({
 *       contentId: productId,
 *       value: 29.99,
 *       currency: 'USD',
 *       autoGenerateEventId: true
 *     });
 *   };
 *
 *   return <button onClick={handleAddToCart}>Add to Cart</button>;
 * }
 * ```
 */
export function useMetaPixel(options: UseMetaPixelOptions = {}): MetaPixelMethods {
  const {
    autoTrackPageView = true,
    debug = false,
    trackRouteChanges = true,
  } = options;

  const previousUrl = useRef<string>('');
  const hasTrackedInitialPageView = useRef<boolean>(false);

  // Enable debug mode if requested
  useEffect(() => {
    if (debug) {
      metaPixel.enableDebugMode();
    } else {
      metaPixel.disableDebugMode();
    }
  }, [debug]);

  // Track page view on mount
  useEffect(() => {
    if (autoTrackPageView && !hasTrackedInitialPageView.current) {
      metaPixel.trackPageView(metaPixel.generateEventId());
      hasTrackedInitialPageView.current = true;
      previousUrl.current = window.location.href;
    }
  }, [autoTrackPageView]);

  // Track route changes for SPAs
  useEffect(() => {
    if (!trackRouteChanges) return;

    const handleRouteChange = () => {
      const currentUrl = window.location.href;

      if (currentUrl !== previousUrl.current) {
        previousUrl.current = currentUrl;
        metaPixel.trackPageView(metaPixel.generateEventId());
      }
    };

    // Listen for history changes (for SPAs)
    window.addEventListener('popstate', handleRouteChange);

    // Listen for hash changes
    window.addEventListener('hashchange', handleRouteChange);

    // Create a MutationObserver to detect URL changes in SPAs
    let lastUrl = window.location.href;
    const observer = new MutationObserver(() => {
      const currentUrl = window.location.href;
      if (currentUrl !== lastUrl) {
        lastUrl = currentUrl;
        handleRouteChange();
      }
    });

    observer.observe(document, { subtree: true, childList: true });

    return () => {
      window.removeEventListener('popstate', handleRouteChange);
      window.removeEventListener('hashchange', handleRouteChange);
      observer.disconnect();
    };
  }, [trackRouteChanges]);

  // Wrapped methods with automatic event ID generation
  const trackPageView = useCallback(() => {
    metaPixel.trackPageView(metaPixel.generateEventId());
  }, []);

  const generateEventId = useCallback(() => {
    return metaPixel.generateEventId();
  }, []);

  const setAdvancedMatching = useCallback(async (userData: UserData) => {
    return metaPixel.setAdvancedMatching(userData);
  }, []);

  const trackViewContent = useCallback((params: {
    contentId: string;
    contentName?: string;
    contentCategory?: string;
    value?: number;
    currency?: string;
    autoGenerateEventId?: boolean;
  }) => {
    const { autoGenerateEventId = true, ...eventParams } = params;
    const eventId = autoGenerateEventId ? metaPixel.generateEventId() : undefined;

    metaPixel.trackViewContent({
      ...eventParams,
      eventId,
    });
  }, []);

  const trackSearch = useCallback((params: {
    searchString: string;
    contentIds?: string[];
    contentCategory?: string;
    autoGenerateEventId?: boolean;
  }) => {
    const { autoGenerateEventId = true, ...eventParams } = params;
    const eventId = autoGenerateEventId ? metaPixel.generateEventId() : undefined;

    metaPixel.trackSearch({
      ...eventParams,
      eventId,
    });
  }, []);

  const trackAddToCart = useCallback((params: {
    contentId: string;
    contentName?: string;
    value: number;
    currency: string;
    autoGenerateEventId?: boolean;
  }) => {
    const { autoGenerateEventId = true, ...eventParams } = params;
    const eventId = autoGenerateEventId ? metaPixel.generateEventId() : undefined;

    metaPixel.trackAddToCart({
      ...eventParams,
      eventId,
    });
  }, []);

  const trackAddToWishlist = useCallback((params: {
    contentId: string;
    contentName?: string;
    value?: number;
    currency?: string;
    autoGenerateEventId?: boolean;
  }) => {
    const { autoGenerateEventId = true, ...eventParams } = params;
    const eventId = autoGenerateEventId ? metaPixel.generateEventId() : undefined;

    metaPixel.trackAddToWishlist({
      ...eventParams,
      eventId,
    });
  }, []);

  const trackInitiateCheckout = useCallback((params: {
    contentIds: string[];
    value: number;
    currency: string;
    numItems: number;
    autoGenerateEventId?: boolean;
  }) => {
    const { autoGenerateEventId = true, ...eventParams } = params;
    const eventId = autoGenerateEventId ? metaPixel.generateEventId() : undefined;

    metaPixel.trackInitiateCheckout({
      ...eventParams,
      eventId,
    });
  }, []);

  const trackAddPaymentInfo = useCallback((params: {
    contentIds?: string[];
    value?: number;
    currency?: string;
    autoGenerateEventId?: boolean;
  }) => {
    const { autoGenerateEventId = true, ...eventParams } = params;
    const eventId = autoGenerateEventId ? metaPixel.generateEventId() : undefined;

    metaPixel.trackAddPaymentInfo({
      ...eventParams,
      eventId,
    });
  }, []);

  const trackPurchase = useCallback((params: PurchaseData & {
    autoGenerateEventId?: boolean;
  }) => {
    const { autoGenerateEventId = true, ...eventParams } = params;
    const eventId = autoGenerateEventId ? metaPixel.generateEventId() : undefined;

    metaPixel.trackPurchase({
      ...eventParams,
      eventId,
    });
  }, []);

  const trackLead = useCallback((params: {
    contentName?: string;
    contentCategory?: string;
    value?: number;
    currency?: string;
    autoGenerateEventId?: boolean;
  }) => {
    const { autoGenerateEventId = true, ...eventParams } = params;
    const eventId = autoGenerateEventId ? metaPixel.generateEventId() : undefined;

    metaPixel.trackLead({
      ...eventParams,
      eventId,
    });
  }, []);

  const trackCompleteRegistration = useCallback((params: {
    contentName?: string;
    status?: string;
    value?: number;
    currency?: string;
    autoGenerateEventId?: boolean;
  }) => {
    const { autoGenerateEventId = true, ...eventParams } = params;
    const eventId = autoGenerateEventId ? metaPixel.generateEventId() : undefined;

    metaPixel.trackCompleteRegistration({
      ...eventParams,
      eventId,
    });
  }, []);

  const trackSubscribe = useCallback((params: {
    value: number;
    currency: string;
    predictedLtv?: number;
    autoGenerateEventId?: boolean;
  }) => {
    const { autoGenerateEventId = true, ...eventParams } = params;
    const eventId = autoGenerateEventId ? metaPixel.generateEventId() : undefined;

    metaPixel.trackSubscribe({
      ...eventParams,
      eventId,
    });
  }, []);

  const trackCustomEvent = useCallback((
    eventName: string,
    params?: Record<string, any>,
    autoGenerateEventId: boolean = true
  ) => {
    const eventId = autoGenerateEventId ? metaPixel.generateEventId() : undefined;
    metaPixel.trackCustomEvent(eventName, params, eventId);
  }, []);

  const isInitialized = useCallback(() => {
    return metaPixel.isInitialized();
  }, []);

  const getPixelId = useCallback(() => {
    return metaPixel.getPixelId();
  }, []);

  return {
    trackPageView,
    generateEventId,
    setAdvancedMatching,
    trackViewContent,
    trackSearch,
    trackAddToCart,
    trackAddToWishlist,
    trackInitiateCheckout,
    trackAddPaymentInfo,
    trackPurchase,
    trackLead,
    trackCompleteRegistration,
    trackSubscribe,
    trackCustomEvent,
    isInitialized,
    getPixelId,
  };
}

export default useMetaPixel;
