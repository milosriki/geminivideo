# AGENT INSTRUCTIONS TEMPLATE
## Best Practices for Technically Excellent Agents

**Use this template for each agent assignment**

---

## 📋 STANDARD INSTRUCTIONS FOR ALL AGENTS

### 1. BEFORE STARTING
- [ ] Read the file you're assigned to modify
- [ ] Understand existing patterns
- [ ] Identify what's missing
- [ ] Plan your changes

### 2. PATTERN MATCHING (CRITICAL)
- ✅ **ALWAYS** copy existing patterns exactly
- ✅ **ALWAYS** match indentation style
- ✅ **ALWAYS** match naming conventions
- ✅ **ALWAYS** match error handling style
- ❌ **NEVER** change existing working code
- ❌ **NEVER** remove functionality
- ❌ **NEVER** change function signatures

### 3. ERROR HANDLING (MANDATORY)
Every function MUST have:
```typescript
// TypeScript/Node.js
try {
  // Implementation
  return result;
} catch (error: any) {
  logger.error(`Error in functionName: ${error.message}`);
  throw error; // or return error response
}
```

```python
# Python
try:
    # Implementation
    return result
except Exception as e:
    logger.error(f"Error in function_name: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

### 4. TESTING
- [ ] Test each new function/endpoint
- [ ] Verify error handling works
- [ ] Verify no existing functionality broken
- [ ] Run existing tests (if available)

### 5. COMMIT FORMAT
```bash
git commit -m "[GROUP-X] Agent Y: [exact description]"
```

Examples:
- `[GROUP-A] Agent 1: Add campaign activation endpoint`
- `[GROUP-B] Agent 5: Wire cross-learner training endpoint`

---

## 🎯 CODE PATTERNS TO COPY

### TypeScript Endpoint Pattern:
```typescript
app.post('/api/resource/:id/action',
  apiRateLimiter,
  validateInput({
    params: { id: { type: 'uuid', required: true } },
    body: { field: { type: 'string', required: true } }
  }),
  async (req: Request, res: Response) => {
    try {
      const { id } = req.params;
      const { field } = req.body;
      
      const result = await pgPool.query(
        'UPDATE table SET field = $1 WHERE id = $2 RETURNING *',
        [field, id]
      );
      
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Resource not found' });
      }
      
      res.json({ success: true, data: result.rows[0] });
    } catch (error: any) {
      logger.error(`Error in action: ${error.message}`);
      res.status(500).json({ error: error.message });
    }
  }
);
```

### Python Endpoint Pattern:
```python
@app.post("/api/resource/{resource_id}/action")
async def action_endpoint(
    resource_id: str,
    request: RequestModel
):
    """
    Description of what this endpoint does
    
    Args:
        resource_id: ID of the resource
        request: Request body model
    
    Returns:
        Response model
    """
    try:
        # Implementation
        result = await some_service.do_action(resource_id, request.data)
        
        return {
            "success": True,
            "data": result
        }
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in action_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
```

### Service Method Pattern:
```typescript
async methodName(params: MethodParams): Promise<MethodResult> {
  try {
    // Validate inputs
    if (!params.requiredField) {
      throw new Error('requiredField is required');
    }
    
    // Implementation
    const result = await this.dependency.call(params);
    
    // Return result
    return {
      success: true,
      data: result
    };
  } catch (error: any) {
    logger.error(`Error in methodName: ${error.message}`);
    throw error;
  }
}
```

---

## ✅ QUALITY CHECKLIST

### Before Committing:
- [ ] Code follows existing patterns exactly
- [ ] Error handling on ALL functions
- [ ] No existing code modified (only additions)
- [ ] No functionality removed
- [ ] Tests pass (if applicable)
- [ ] Code is readable and well-commented
- [ ] Commit message follows format

### Code Review Checklist:
- [ ] Matches existing style
- [ ] Error handling present
- [ ] No breaking changes
- [ ] Functionality preserved
- [ ] Performance acceptable

---

## 🚫 WHAT NOT TO DO

### ❌ DON'T:
1. Change existing working code
2. Remove any functionality
3. Change function signatures
4. Use different patterns than existing code
5. Skip error handling
6. Commit without testing
7. Use different naming conventions
8. Change database schemas
9. Modify configuration unnecessarily
10. Break existing tests

### ✅ DO:
1. Add missing functionality
2. Copy existing patterns exactly
3. Add error handling to everything
4. Test before committing
5. Follow existing conventions
6. Preserve all functionality
7. Document your changes
8. Use consistent formatting

---

## 📝 EXAMPLE: Adding an Endpoint

### Step 1: Find Similar Endpoint
```typescript
// Existing endpoint
app.post('/api/campaigns',
  apiRateLimiter,
  validateInput({ body: { name: { type: 'string', required: true } } }),
  async (req: Request, res: Response) => {
    try {
      const { name } = req.body;
      const result = await pgPool.query(
        'INSERT INTO campaigns (name) VALUES ($1) RETURNING *',
        [name]
      );
      res.json({ success: true, data: result.rows[0] });
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  }
);
```

### Step 2: Copy Pattern for New Endpoint
```typescript
// New endpoint (copy pattern exactly)
app.post('/api/campaigns/:id/activate',
  apiRateLimiter,
  validateInput({ params: { id: { type: 'uuid', required: true } } }),
  async (req: Request, res: Response) => {
    try {
      const { id } = req.params;
      const result = await pgPool.query(
        'UPDATE campaigns SET status = $1 WHERE id = $2 RETURNING *',
        ['active', id]
      );
      if (result.rows.length === 0) {
        return res.status(404).json({ error: 'Campaign not found' });
      }
      res.json({ success: true, data: result.rows[0] });
    } catch (error: any) {
      res.status(500).json({ error: error.message });
    }
  }
);
```

### Step 3: Test
```bash
# Test the endpoint
curl -X POST http://localhost:8000/api/campaigns/{id}/activate
```

### Step 4: Commit
```bash
git add services/gateway-api/src/routes/campaigns.ts
git commit -m "[GROUP-A] Agent 1: Add campaign activation endpoint"
```

---

## 🎯 SUCCESS CRITERIA

### Your work is successful if:
1. ✅ All missing functionality added
2. ✅ All code follows existing patterns
3. ✅ All functions have error handling
4. ✅ No existing functionality broken
5. ✅ All tests pass
6. ✅ Code is clean and readable
7. ✅ Commit message is clear

---

**FOLLOW THIS TEMPLATE FOR ALL AGENT ASSIGNMENTS!** 🚀

