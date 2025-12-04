# AI Credits Endpoint Implementation

## Summary
Successfully added AI credits tracking system to the Gateway API at `/home/user/geminivideo/services/gateway-api/src/index.ts`.

## What Was Added

### 1. Database Tables
Two new tables are automatically created on startup:

#### `ai_credits` table
- `user_id` (VARCHAR, PRIMARY KEY)
- `total_credits` (INTEGER, default 10000)
- `used_credits` (INTEGER, default 0)
- `created_at` (TIMESTAMP)
- `updated_at` (TIMESTAMP)

#### `ai_credit_usage` table
- `id` (SERIAL PRIMARY KEY)
- `user_id` (VARCHAR)
- `credits_used` (INTEGER)
- `operation` (VARCHAR) - e.g., 'video_generation', 'video_analysis'
- `metadata` (JSONB) - additional operation details
- `created_at` (TIMESTAMP)

### 2. API Endpoints

#### GET /api/credits
Returns user's AI credit balance and usage history.

**Query Parameters:**
- `user_id` (optional, defaults to 'default_user')

**Response Format:**
```json
{
  "credits": {
    "available": 8500,
    "total": 10000,
    "used": 1500,
    "usage_history": [
      {
        "date": "2024-12-01",
        "used": 500,
        "operation": "video_generation",
        "duration": 30,
        "quality": "hd"
      },
      {
        "date": "2024-12-02",
        "used": 300,
        "operation": "video_analysis",
        "clips_analyzed": 5
      }
    ]
  }
}
```

#### POST /api/credits/deduct
Deducts credits from a user's balance (internal use).

**Request Body:**
```json
{
  "user_id": "default_user",
  "credits": 100,
  "operation": "video_generation",
  "metadata": {
    "duration": 30,
    "quality": "hd"
  }
}
```

**Response:**
```json
{
  "message": "Credits deducted successfully",
  "credits": {
    "available": 8400,
    "total": 10000,
    "used": 1600
  }
}
```

### 3. Seed Data
The system automatically seeds sample data for the default user on first startup:
- Total credits: 10,000
- Used credits: 1,500
- Available: 8,500
- 5 sample usage records with different operations

## Files Modified/Created

### Modified
- `/home/user/geminivideo/services/gateway-api/src/index.ts`
  - Added table initialization (lines 142-196)
  - Added GET /api/credits endpoint (lines 2387-2479)
  - Added POST /api/credits/deduct endpoint (lines 2481-2568)

### Created
- `/home/user/geminivideo/database_migrations/003_ai_credits.sql` - Migration file
- `/home/user/geminivideo/services/gateway-api/src/credits-endpoint.ts` - Reference implementation
- `/home/user/geminivideo/services/gateway-api/AI_CREDITS_IMPLEMENTATION.md` - This file

## Testing

### Test the endpoint with curl:
```bash
# Get credits for default user
curl http://localhost:8000/api/credits

# Get credits for specific user
curl http://localhost:8000/api/credits?user_id=default_user

# Deduct credits (internal use)
curl -X POST http://localhost:8000/api/credits/deduct \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "default_user",
    "credits": 100,
    "operation": "video_generation",
    "metadata": {"duration": 30, "quality": "hd"}
  }'
```

### Expected Output:
```json
{
  "credits": {
    "available": 8500,
    "total": 10000,
    "used": 1500,
    "usage_history": [
      {"date": "2024-12-03", "used": 500, "operation": "video_generation", "duration": 30, "quality": "hd"},
      {"date": "2024-12-02", "used": 300, "operation": "video_analysis", "clips_analyzed": 5},
      {"date": "2024-12-02", "used": 200, "operation": "script_generation", "variants": 3},
      {"date": "2024-12-03", "used": 400, "operation": "video_generation", "duration": 60, "quality": "4k"},
      {"date": "2024-12-03", "used": 100, "operation": "text_analysis", "words": 500}
    ]
  }
}
```

## Database Migration
If you need to manually create the tables, run:
```bash
psql $DATABASE_URL -f /home/user/geminivideo/database_migrations/003_ai_credits.sql
```

## Features
- ✅ Automatic table creation on startup
- ✅ Default user with seed data
- ✅ Credit balance tracking
- ✅ Usage history with metadata
- ✅ Credit deduction with validation
- ✅ Insufficient credits error handling
- ✅ Last 30 days of usage history
- ✅ User auto-creation on first access

## Notes
- Uses `default_user` as the default user_id since authentication is not yet implemented
- Credits are tracked per operation with full metadata support
- The system prevents deducting more credits than available (returns 402 error)
- All timestamps use PostgreSQL NOW() for consistency
- Usage history is grouped by date and operation for efficient retrieval
