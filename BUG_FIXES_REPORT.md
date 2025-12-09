# 🐛 BUG FIXES REPORT
## All Errors, Mismatches, and Issues Fixed

**Date:** 2025-01-08  
**Status:** ✅ All Critical Bugs Fixed

---

## 🔴 CRITICAL BUGS FOUND & FIXED

### **BUG 1: Celery Tasks Using Async/Await Incorrectly** ✅ FIXED

**Problem:**
- Celery tasks are regular functions, not async
- Code was using `await` directly in sync functions
- Would cause `RuntimeError: await outside async function`

**Files:**
- `services/ml-service/src/celery_tasks.py`

**Fix:**
- Wrapped async code in `asyncio.run()` for sync Celery tasks
- Fixed `monitor_all_ads_fatigue()` - now uses `asyncio.run(_monitor())`
- Fixed `auto_index_winner()` - now uses `asyncio.run(_index())`
- Fixed `process_hubspot_webhook()` - now uses `asyncio.run(_process())`

**Before:**
```python
@celery_app.task(name='monitor_fatigue')
def monitor_all_ads_fatigue():
    pool = await asyncpg.create_pool(...)  # ❌ ERROR
    ads = await repo.get_all_active()      # ❌ ERROR
```

**After:**
```python
@celery_app.task(name='monitor_fatigue')
def monitor_all_ads_fatigue():
    async def _monitor():
        pool = await asyncpg.create_pool(...)  # ✅ OK
        ads = await repo.get_all_active()      # ✅ OK
    return asyncio.run(_monitor())  # ✅ FIXED
```

---

### **BUG 2: FatigueDetector Interface Mismatch** ✅ FIXED

**Problem:**
- Code was calling `detector.analyze(ad)` 
- Actual function is `detect_fatigue(ad_id, metrics_history)`
- Wrong interface caused `AttributeError`

**Fix:**
- Changed to use correct function: `detect_fatigue(ad_id, metrics_history)`
- Built metrics_history from AdState
- Used correct result structure: `result.status` not `result.fatigue_level`

**Before:**
```python
detector = FatigueDetector()
result = detector.analyze(ad)  # ❌ WRONG
if result.fatigue_level == 'critical':  # ❌ WRONG
```

**After:**
```python
from .fatigue_detector import detect_fatigue
metrics_history = [{'ctr': ..., 'frequency': ..., ...}]
result = detect_fatigue(ad.ad_id, metrics_history)  # ✅ CORRECT
if result.status == 'AUDIENCE_EXHAUSTED':  # ✅ CORRECT
```

---

### **BUG 3: SyntheticRevenue Interface Mismatch** ✅ FIXED

**Problem:**
- Code was calling `calc.calculate(stage_id, deal_amount)`
- Actual method is `calculate_stage_change(tenant_id, stage_from, stage_to, deal_value)`
- Wrong parameters caused `TypeError`

**Fix:**
- Changed to use correct method signature
- Added `tenant_id` parameter
- Used `stage_from` and `stage_to` instead of just `stage_id`
- Used `calculated_value` from result (not `final_synthetic_value`)

**Before:**
```python
result = calc.calculate(
    stage_id=stage_to,
    deal_amount=deal_value
)  # ❌ WRONG METHOD
```

**After:**
```python
result = calc.calculate_stage_change(
    tenant_id=tenant_id,
    stage_from=stage_from,
    stage_to=stage_to,
    deal_value=deal_value
)  # ✅ CORRECT
```

---

### **BUG 4: HubSpotAttribution Interface Mismatch** ✅ FIXED

**Problem:**
- Code was calling `attribution.attribute_conversion(tenant_id, conversion_id, ...)`
- Actual method is `attribute_conversion(tenant_id, conversion_data: ConversionData)`
- Wrong parameters caused `TypeError`

**Fix:**
- Created `ConversionData` object with all required fields
- Passed as single parameter: `conversion_data=conversion`
- Used correct result structure: `attribution_result.ad_id`

**Before:**
```python
attribution_result = attribution.attribute_conversion(
    tenant_id=tenant_id,
    conversion_id=deal_id,
    conversion_value=result.final_synthetic_value,
    conversion_type=f'deal_{stage_to}'
)  # ❌ WRONG SIGNATURE
```

**After:**
```python
conversion = ConversionData(
    conversion_id=deal_id,
    conversion_type=f'deal_{stage_to}',
    conversion_value=result.calculated_value,
    fingerprint_hash=webhook_payload.get('fingerprint_hash'),
    ip_address=webhook_payload.get('ip_address'),
    user_agent=webhook_payload.get('user_agent'),
    conversion_timestamp=datetime.now(timezone.utc),
    fbclid=webhook_payload.get('fbclid'),
    click_id=webhook_payload.get('click_id')
)
attribution_result = attribution_service.attribute_conversion(
    tenant_id=tenant_id,
    conversion_data=conversion
)  # ✅ CORRECT
```

---

### **BUG 5: WinnerIndex Interface Mismatch** ✅ FIXED

**Problem:**
- Code was calling `await index.add_winner(ad_id, embedding, metadata)`
- Actual method is sync: `index.add_winner(ad_id, embedding: np.ndarray, metadata)`
- Wrong type: embedding must be `np.ndarray`, not list
- Wrong context: not async

**Fix:**
- Removed `await` (method is sync)
- Converted embedding to `np.ndarray`
- Used correct method signature
- Called `index.persist()` after adding

**Before:**
```python
embedding = await generate_creative_dna_embedding(creative_dna)  # List
await index.add_winner(ad_id, embedding, metadata)  # ❌ WRONG
```

**After:**
```python
embedding = await generate_creative_dna_embedding(creative_dna)  # List
index = get_winner_index()
success = index.add_winner(
    ad_id=ad_id,
    embedding=np.array(embedding),  # ✅ Convert to np.ndarray
    metadata=creative_dna
)
index.persist()  # ✅ Save to disk
```

---

### **BUG 6: Missing Import Statements** ✅ FIXED

**Problems:**
- Missing `import os` in celery_tasks.py
- Missing `import httpx` for HTTP calls
- Missing `import asyncio` for async wrapper

**Fix:**
- Added all required imports
- Added fallback for missing embedding service

---

## ✅ ALL BUGS FIXED

### **Summary:**
- ✅ 6 critical bugs identified
- ✅ All bugs fixed
- ✅ All interfaces corrected
- ✅ All async/sync issues resolved
- ✅ All type mismatches fixed

### **Files Fixed:**
1. `services/ml-service/src/celery_tasks.py` - All 3 tasks fixed

### **Testing:**
- [ ] Run Celery worker: `celery -A src.celery_app worker`
- [ ] Test webhook task: Queue test payload
- [ ] Test fatigue monitoring: Run periodic task
- [ ] Test auto-indexing: Queue winner data

---

## 🧪 VERIFICATION STEPS

### **1. Test Celery Tasks:**
```bash
# Start worker
celery -A src.celery_app worker -l info

# Test in Python shell
from src.celery_tasks import process_hubspot_webhook
result = process_hubspot_webhook.delay({
    'dealId': '123',
    'stageTo': 'assessment_booked',
    'tenantId': 'test'
})
```

### **2. Test Fatigue Monitoring:**
```bash
# Run task
celery -A src.celery_app call src.celery_tasks.monitor_fatigue
```

### **3. Test Auto-Indexing:**
```bash
# Run task
celery -A src.celery_app call src.celery_tasks.auto_index_winner \
  --args='["test-123", {"hook_type": "testimonial"}]'
```

---

**All bugs fixed! Code ready for testing! ✅**

