// Type declaration for facebook-nodejs-business-sdk
// Using loose typing to avoid complex SDK type definitions
declare module 'facebook-nodejs-business-sdk' {
  export class FacebookAdsApi {
    static init(accessToken: string): any;
    static setDebug(debug: boolean): void;
  }
  
  export class AdAccount {
    constructor(id: string);
    [key: string]: any;
  }
  
  export class Campaign {
    constructor(id?: string);
    [key: string]: any;
  }
  
  export class AdSet {
    constructor(id?: string);
    [key: string]: any;
  }
  
  export class Ad {
    constructor(id?: string);
    [key: string]: any;
  }
  
  export class AdCreative {
    constructor(id?: string);
    [key: string]: any;
  }
  
  export class AdVideo {
    constructor(id?: string);
    [key: string]: any;
  }
}


