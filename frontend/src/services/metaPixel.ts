/**
 * Meta Pixel Service with Advanced Matching
 * Provides client-side tracking for Facebook/Meta advertising platform
 *
 * Features:
 * - Client-side SHA256 hashing for advanced matching
 * - Event ID generation for CAPI deduplication
 * - Standard and custom event tracking
 * - Debug mode support
 * - TypeScript type safety
 */

declare global {
  interface Window {
    fbq: any;
    _fbq: any;
  }
}

interface UserData {
  email?: string;
  phone?: string;
  firstName?: string;
  lastName?: string;
  city?: string;
  state?: string;
  zipCode?: string;
  country?: string;
  externalId?: string;
  dateOfBirth?: string;
  gender?: 'm' | 'f';
}

interface ContentInfo {
  content_ids?: string[];
  content_type?: 'product' | 'product_group';
  content_name?: string;
  content_category?: string;
  contents?: Array<{
    id: string;
    quantity: number;
    item_price?: number;
  }>;
}

interface PurchaseData extends ContentInfo {
  value: number;
  currency: string;
  num_items?: number;
}

interface HashedUserData {
  em?: string;
  ph?: string;
  fn?: string;
  ln?: string;
  ct?: string;
  st?: string;
  zp?: string;
  country?: string;
  external_id?: string;
  db?: string;
  ge?: string;
}

class MetaPixelService {
  private pixelId: string;
  private initialized: boolean = false;
  private userData: UserData | null = null;
  private hashedUserData: HashedUserData | null = null;
  private debugMode: boolean = false;

  constructor() {
    this.pixelId = import.meta.env.VITE_META_PIXEL_ID || '';
  }

  /**
   * Initialize Meta Pixel
   * Loads the Facebook Pixel script and sets up tracking
   */
  initPixel(pixelId?: string): void {
    if (this.initialized) {
      console.warn('[MetaPixel] Already initialized');
      return;
    }

    const id = pixelId || this.pixelId;

    if (!id) {
      console.error('[MetaPixel] No Pixel ID provided');
      return;
    }

    this.pixelId = id;

    // Load Facebook Pixel script
    /* eslint-disable */
    (function (f: any, b: any, e: any, v: any, n?: any, t?: any, s?: any) {
      if (f.fbq !== undefined) return;
      n = f.fbq = function () {
        n.callMethod
          ? n.callMethod.apply(n, arguments)
          : n.queue.push(arguments);
      };
      if (!f._fbq) f._fbq = n;
      n.push = n;
      n.loaded = !0;
      n.version = '2.0';
      n.queue = [];
      t = b.createElement(e);
      t.async = !0;
      t.src = v;
      s = b.getElementsByTagName(e)[0];
      s.parentNode.insertBefore(t, s);
    })(
      window,
      document,
      'script',
      'https://connect.facebook.net/en_US/fbevents.js'
    );
    /* eslint-enable */

    // Initialize pixel with advanced matching if available
    if (this.hashedUserData) {
      window.fbq('init', this.pixelId, this.hashedUserData);
    } else {
      window.fbq('init', this.pixelId);
    }

    // Track automatic page view
    window.fbq('track', 'PageView');

    this.initialized = true;

    if (this.debugMode) {
      console.log('[MetaPixel] Initialized with ID:', this.pixelId);
    }
  }

  /**
   * Set user data for advanced matching
   * Hashes PII client-side using SHA256
   */
  async setAdvancedMatching(userData: UserData): Promise<void> {
    this.userData = userData;
    this.hashedUserData = await this.hashUserData(userData);

    if (this.initialized && window.fbq) {
      // Update pixel with advanced matching data
      window.fbq('init', this.pixelId, this.hashedUserData);
    }

    if (this.debugMode) {
      console.log('[MetaPixel] Advanced matching data set');
    }
  }

  /**
   * Hash user data for advanced matching
   * Uses SHA256 for PII fields
   */
  private async hashUserData(userData: UserData): Promise<HashedUserData> {
    const hashed: HashedUserData = {};

    if (userData.email) {
      hashed.em = await this.sha256(this.normalizeEmail(userData.email));
    }
    if (userData.phone) {
      hashed.ph = await this.sha256(this.normalizePhone(userData.phone));
    }
    if (userData.firstName) {
      hashed.fn = await this.sha256(this.normalizeString(userData.firstName));
    }
    if (userData.lastName) {
      hashed.ln = await this.sha256(this.normalizeString(userData.lastName));
    }
    if (userData.city) {
      hashed.ct = await this.sha256(this.normalizeString(userData.city));
    }
    if (userData.state) {
      hashed.st = await this.sha256(this.normalizeString(userData.state));
    }
    if (userData.zipCode) {
      hashed.zp = await this.sha256(this.normalizeString(userData.zipCode));
    }
    if (userData.country) {
      hashed.country = await this.sha256(this.normalizeString(userData.country));
    }
    if (userData.externalId) {
      hashed.external_id = await this.sha256(userData.externalId);
    }
    if (userData.dateOfBirth) {
      hashed.db = await this.sha256(this.normalizeDate(userData.dateOfBirth));
    }
    if (userData.gender) {
      hashed.ge = await this.sha256(userData.gender);
    }

    return hashed;
  }

  /**
   * Client-side SHA256 hashing using Web Crypto API
   */
  private async sha256(message: string): Promise<string> {
    const msgBuffer = new TextEncoder().encode(message);
    const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    const hashHex = hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    return hashHex;
  }

  /**
   * Normalize email for hashing
   */
  private normalizeEmail(email: string): string {
    return email.toLowerCase().trim();
  }

  /**
   * Normalize phone for hashing (remove non-digits)
   */
  private normalizePhone(phone: string): string {
    return phone.replace(/\D/g, '');
  }

  /**
   * Normalize string for hashing
   */
  private normalizeString(str: string): string {
    return str.toLowerCase().trim().replace(/\s+/g, '');
  }

  /**
   * Normalize date for hashing (YYYYMMDD format)
   */
  private normalizeDate(date: string): string {
    return date.replace(/\D/g, '');
  }

  /**
   * Generate event ID for CAPI deduplication
   * Returns a UUID v4
   */
  generateEventId(): string {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
  }

  /**
   * Track standard event with optional event ID
   */
  private trackEvent(
    eventName: string,
    params?: Record<string, any>,
    eventId?: string
  ): void {
    if (!this.initialized || typeof window.fbq === 'undefined') {
      console.warn('[MetaPixel] Not initialized. Call initPixel() first.');
      return;
    }

    const options: Record<string, any> = {};
    if (eventId) {
      options.eventID = eventId;
    }

    if (this.debugMode) {
      // console.log('[MetaPixel] Track:', eventName, params, options);
    }

    if (params) {
      window.fbq('track', eventName, params, options);
    } else {
      window.fbq('track', eventName, options);
    }
  }

  /**
   * Track page view
   */
  trackPageView(eventId?: string): void {
    this.trackEvent('PageView', undefined, eventId);
  }

  /**
   * Track view content event
   */
  trackViewContent(params: {
    contentId: string;
    contentName?: string;
    contentCategory?: string;
    value?: number;
    currency?: string;
    eventId?: string;
  }): void {
    const { eventId, ...eventParams } = params;

    const trackParams: Record<string, any> = {
      content_ids: [params.contentId],
      content_type: 'product',
    };

    if (params.contentName) trackParams.content_name = params.contentName;
    if (params.contentCategory) trackParams.content_category = params.contentCategory;
    if (params.value) trackParams.value = params.value;
    if (params.currency) trackParams.currency = params.currency;

    this.trackEvent('ViewContent', trackParams, eventId);
  }

  /**
   * Track search event
   */
  trackSearch(params: {
    searchString: string;
    contentIds?: string[];
    contentCategory?: string;
    eventId?: string;
  }): void {
    const { eventId, ...eventParams } = params;

    const trackParams: Record<string, any> = {
      search_string: params.searchString,
    };

    if (params.contentIds) trackParams.content_ids = params.contentIds;
    if (params.contentCategory) trackParams.content_category = params.contentCategory;

    this.trackEvent('Search', trackParams, eventId);
  }

  /**
   * Track add to cart event
   */
  trackAddToCart(params: {
    contentId: string;
    contentName?: string;
    value: number;
    currency: string;
    eventId?: string;
  }): void {
    const { eventId, ...eventParams } = params;

    const trackParams: Record<string, any> = {
      content_ids: [params.contentId],
      content_type: 'product',
      value: params.value,
      currency: params.currency,
    };

    if (params.contentName) trackParams.content_name = params.contentName;

    this.trackEvent('AddToCart', trackParams, eventId);
  }

  /**
   * Track add to wishlist event
   */
  trackAddToWishlist(params: {
    contentId: string;
    contentName?: string;
    value?: number;
    currency?: string;
    eventId?: string;
  }): void {
    const { eventId, ...eventParams } = params;

    const trackParams: Record<string, any> = {
      content_ids: [params.contentId],
      content_type: 'product',
    };

    if (params.contentName) trackParams.content_name = params.contentName;
    if (params.value) trackParams.value = params.value;
    if (params.currency) trackParams.currency = params.currency;

    this.trackEvent('AddToWishlist', trackParams, eventId);
  }

  /**
   * Track initiate checkout event
   */
  trackInitiateCheckout(params: {
    contentIds: string[];
    value: number;
    currency: string;
    numItems: number;
    eventId?: string;
  }): void {
    const { eventId, ...eventParams } = params;

    const trackParams = {
      content_ids: params.contentIds,
      content_type: 'product' as const,
      value: params.value,
      currency: params.currency,
      num_items: params.numItems,
    };

    this.trackEvent('InitiateCheckout', trackParams, eventId);
  }

  /**
   * Track add payment info event
   */
  trackAddPaymentInfo(params: {
    contentIds?: string[];
    value?: number;
    currency?: string;
    eventId?: string;
  }): void {
    const { eventId, ...eventParams } = params;

    const trackParams: Record<string, any> = {
      content_type: 'product',
    };

    if (params.contentIds) trackParams.content_ids = params.contentIds;
    if (params.value) trackParams.value = params.value;
    if (params.currency) trackParams.currency = params.currency;

    this.trackEvent('AddPaymentInfo', trackParams, eventId);
  }

  /**
   * Track purchase event
   */
  trackPurchase(params: PurchaseData & { eventId?: string }): void {
    const { eventId, ...eventParams } = params;

    const trackParams: Record<string, any> = {
      value: params.value,
      currency: params.currency,
    };

    if (params.content_ids) trackParams.content_ids = params.content_ids;
    if (params.content_type) trackParams.content_type = params.content_type;
    if (params.content_name) trackParams.content_name = params.content_name;
    if (params.content_category) trackParams.content_category = params.content_category;
    if (params.contents) trackParams.contents = params.contents;
    if (params.num_items) trackParams.num_items = params.num_items;

    this.trackEvent('Purchase', trackParams, eventId);
  }

  /**
   * Track lead event
   */
  trackLead(params: {
    contentName?: string;
    contentCategory?: string;
    value?: number;
    currency?: string;
    eventId?: string;
  }): void {
    const { eventId, ...eventParams } = params;

    const trackParams: Record<string, any> = {};

    if (params.contentName) trackParams.content_name = params.contentName;
    if (params.contentCategory) trackParams.content_category = params.contentCategory;
    if (params.value) trackParams.value = params.value;
    if (params.currency) trackParams.currency = params.currency;

    this.trackEvent('Lead', trackParams, eventId);
  }

  /**
   * Track complete registration event
   */
  trackCompleteRegistration(params: {
    contentName?: string;
    status?: string;
    value?: number;
    currency?: string;
    eventId?: string;
  }): void {
    const { eventId, ...eventParams } = params;

    const trackParams: Record<string, any> = {};

    if (params.contentName) trackParams.content_name = params.contentName;
    if (params.status) trackParams.status = params.status;
    if (params.value) trackParams.value = params.value;
    if (params.currency) trackParams.currency = params.currency;

    this.trackEvent('CompleteRegistration', trackParams, eventId);
  }

  /**
   * Track subscribe event
   */
  trackSubscribe(params: {
    value: number;
    currency: string;
    predictedLtv?: number;
    eventId?: string;
  }): void {
    const { eventId, ...eventParams } = params;

    const trackParams: Record<string, any> = {
      value: params.value,
      currency: params.currency,
    };

    if (params.predictedLtv) trackParams.predicted_ltv = params.predictedLtv;

    this.trackEvent('Subscribe', trackParams, eventId);
  }

  /**
   * Track custom event
   */
  trackCustomEvent(
    eventName: string,
    params?: Record<string, any>,
    eventId?: string
  ): void {
    if (!this.initialized || typeof window.fbq === 'undefined') {
      console.warn('[MetaPixel] Not initialized. Call initPixel() first.');
      return;
    }

    const options: Record<string, any> = {};
    if (eventId) {
      options.eventID = eventId;
    }

    if (this.debugMode) {
      // console.log('[MetaPixel] TrackCustom:', eventName, params, options);
    }

    if (params) {
      window.fbq('trackCustom', eventName, params, options);
    } else {
      window.fbq('trackCustom', eventName, options);
    }
  }

  /**
   * Check if pixel is initialized
   */
  isInitialized(): boolean {
    return this.initialized;
  }

  /**
   * Get current pixel ID
   */
  getPixelId(): string {
    return this.pixelId;
  }

  /**
   * Enable debug mode
   */
  enableDebugMode(): void {
    this.debugMode = true;
    // console.log('[MetaPixel] Debug mode enabled');
  }

  /**
   * Disable debug mode
   */
  disableDebugMode(): void {
    this.debugMode = false;
  }
}

// Export singleton instance
export const metaPixel = new MetaPixelService();

// Export class for testing or multiple instances
export default MetaPixelService;

// Export types
export type {
  UserData,
  ContentInfo,
  PurchaseData,
};
