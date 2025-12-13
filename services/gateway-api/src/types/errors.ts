export enum ErrorCode {
  // General errors
  INTERNAL_ERROR = 'INTERNAL_ERROR',
  VALIDATION_ERROR = 'VALIDATION_ERROR',
  NOT_FOUND = 'NOT_FOUND',
  UNAUTHORIZED = 'UNAUTHORIZED',
  FORBIDDEN = 'FORBIDDEN',

  // Domain-specific errors
  AD_NOT_FOUND = 'AD_NOT_FOUND',
  CAMPAIGN_NOT_FOUND = 'CAMPAIGN_NOT_FOUND',
  INVALID_AD_STATUS = 'INVALID_AD_STATUS',
  BUDGET_EXCEEDED = 'BUDGET_EXCEEDED',

  // External API errors
  META_API_ERROR = 'META_API_ERROR',
  HUBSPOT_API_ERROR = 'HUBSPOT_API_ERROR',
  GOOGLE_API_ERROR = 'GOOGLE_API_ERROR',
}

export class AppError extends Error {
  constructor(
    public code: ErrorCode,
    public message: string,
    public statusCode: number = 500,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'AppError';
    Error.captureStackTrace(this, this.constructor);
  }
}
