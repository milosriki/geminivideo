# Error Handling Guide

This guide explains how to use the standardized error handling system in the Gateway API.

## Overview

The error handling system provides:
- **Consistent error responses** across all endpoints
- **Type-safe error codes** using TypeScript enums
- **Detailed error information** with optional context
- **Request tracking** via request IDs

## Error Response Format

All errors follow this standardized format:

```typescript
{
  success: false,
  error: {
    code: ErrorCode,           // Enum value for programmatic handling
    message: string,            // Human-readable error message
    details?: object,           // Optional additional context
    requestId?: string          // Request ID for tracking
  }
}
```

## Error Codes

Available error codes in `ErrorCode` enum:

### General Errors
- `INTERNAL_ERROR` - Server-side errors (500)
- `VALIDATION_ERROR` - Invalid request data (400)
- `NOT_FOUND` - Resource not found (404)
- `UNAUTHORIZED` - Authentication required (401)
- `FORBIDDEN` - Insufficient permissions (403)

### Domain-Specific Errors
- `AD_NOT_FOUND` - Advertisement not found
- `CAMPAIGN_NOT_FOUND` - Campaign not found
- `INVALID_AD_STATUS` - Invalid advertisement status
- `BUDGET_EXCEEDED` - Budget limit exceeded

### External API Errors
- `META_API_ERROR` - Facebook/Meta API error
- `HUBSPOT_API_ERROR` - HubSpot API error
- `GOOGLE_API_ERROR` - Google API error

## Usage Examples

### 1. Throwing Errors in Routes

```typescript
import { AppError, ErrorCode } from '../types/errors';

// Example: Campaign not found
app.get('/api/campaigns/:id', async (req, res, next) => {
  try {
    const campaign = await getCampaign(req.params.id);

    if (!campaign) {
      throw new AppError(
        ErrorCode.CAMPAIGN_NOT_FOUND,
        'Campaign not found',
        404,
        { campaignId: req.params.id }
      );
    }

    res.json({ success: true, data: campaign });
  } catch (error) {
    next(error); // Pass to error handler middleware
  }
});
```

### 2. Validation Errors

```typescript
import { AppError, ErrorCode } from '../types/errors';

app.post('/api/ads', async (req, res, next) => {
  try {
    const { title, budget } = req.body;

    if (!title || !budget) {
      throw new AppError(
        ErrorCode.VALIDATION_ERROR,
        'Missing required fields',
        400,
        {
          required: ['title', 'budget'],
          received: Object.keys(req.body)
        }
      );
    }

    if (budget < 0) {
      throw new AppError(
        ErrorCode.VALIDATION_ERROR,
        'Budget must be positive',
        400,
        { budget }
      );
    }

    // Create ad...
    res.json({ success: true, data: ad });
  } catch (error) {
    next(error);
  }
});
```

### 3. External API Errors

```typescript
import { AppError, ErrorCode } from '../types/errors';

async function createMetaAd(adData: any) {
  try {
    const result = await metaApi.createAd(adData);
    return result;
  } catch (error: any) {
    throw new AppError(
      ErrorCode.META_API_ERROR,
      'Failed to create ad on Meta platform',
      502,
      {
        originalError: error.message,
        metaErrorCode: error.code
      }
    );
  }
}
```

### 4. Authorization Errors

The auth middleware automatically uses the standardized format:

```typescript
import { authenticateUser, requireRole, UserRole } from '../middleware/auth';

// Requires authentication
app.get('/api/admin/stats',
  authenticateUser,
  requireRole(UserRole.ADMIN),
  async (req, res) => {
    // Only admins can access
  }
);
```

### 5. Using with Async Handler

The error handler middleware automatically catches errors from async functions:

```typescript
import { asyncHandler } from '../middleware/error-handler';

app.get('/api/data', asyncHandler(async (req, res) => {
  // Errors are automatically caught and passed to error handler
  const data = await fetchData();
  res.json({ success: true, data });
}));
```

## Client-Side Error Handling

Example of handling errors on the client:

```typescript
async function fetchCampaign(id: string) {
  const response = await fetch(`/api/campaigns/${id}`);
  const data = await response.json();

  if (!data.success) {
    // Handle error based on code
    switch (data.error.code) {
      case 'CAMPAIGN_NOT_FOUND':
        showNotification('Campaign not found');
        break;
      case 'UNAUTHORIZED':
        redirectToLogin();
        break;
      case 'BUDGET_EXCEEDED':
        showBudgetWarning(data.error.details);
        break;
      default:
        showGenericError(data.error.message);
    }
    return null;
  }

  return data.data;
}
```

## Adding New Error Codes

To add a new error code:

1. Add to the `ErrorCode` enum in `types/errors.ts`:
```typescript
export enum ErrorCode {
  // ... existing codes
  MY_NEW_ERROR = 'MY_NEW_ERROR',
}
```

2. Use in your code:
```typescript
throw new AppError(
  ErrorCode.MY_NEW_ERROR,
  'Description of the error',
  statusCode,
  optionalDetails
);
```

## Best Practices

1. **Use specific error codes** - Choose the most specific error code for better client handling
2. **Provide helpful details** - Include context that helps debugging without exposing sensitive data
3. **Use appropriate status codes** - Match HTTP status codes to error types
4. **Never expose secrets** - Don't include API keys, tokens, or passwords in error details
5. **Log server errors** - The error handler automatically logs 500+ errors for monitoring
6. **Use next(error)** - Always pass errors to the error handler middleware

## Error Handler Middleware

The error handler is automatically applied in the Express app:

```typescript
import { errorHandler, notFoundHandler } from './middleware/error-handler';

// ... routes

app.use(notFoundHandler);  // Handles 404s
app.use(errorHandler);     // Handles all other errors
```

This ensures all errors are formatted consistently.
