# Demo Mode - Quick Start Guide

## 🚀 Quick Test (5 minutes)

### 1. Start the Backend

```bash
cd /home/user/geminivideo/services/gateway-api

# Install dependencies (if needed)
npm install

# Start the server
npm run dev
```

Backend should be running on `http://localhost:8000`

### 2. Start the Frontend

```bash
cd /home/user/geminivideo/frontend

# Install dependencies (if needed)
npm install

# Start the dev server
npm run dev
```

Frontend should be running on `http://localhost:5173`

### 3. Test Demo Mode

#### Option A: URL Parameter (Recommended)
1. Open browser to: `http://localhost:5173/?demo=true`
2. You should see a purple "Demo Mode" badge in the bottom-right corner
3. Navigate to any page - data will come from demo endpoints

#### Option B: Enable Manually
1. Open browser to: `http://localhost:5173/`
2. Open browser console (F12)
3. Run: `localStorage.setItem('demo_mode_enabled', 'true')`
4. Refresh the page
5. Demo mode badge should appear

### 4. Test Investor Presentation

1. Navigate to: `http://localhost:5173/demo/presentation`
2. Press `F` to enter fullscreen
3. Use arrow keys (← →) to navigate slides
4. Press `ESC` to exit

---

## 🧪 Test Demo API Endpoints

### Check Demo Status
```bash
curl http://localhost:8000/api/demo/status
```

**Expected Response**:
```json
{
  "available": true,
  "version": "1.0.0",
  "features": [
    "Impressive campaign metrics",
    "Live-updating charts",
    "AI Council scoring",
    "A/B test with Thompson Sampling",
    "ROAS prediction accuracy",
    "Multi-platform comparison"
  ],
  "message": "Demo mode ready for investor presentation"
}
```

### Get Demo Campaigns
```bash
curl http://localhost:8000/api/demo/campaigns
```

**Expected**: JSON with 4 demo campaigns, each with impressive metrics

### Get Presentation Stats
```bash
curl http://localhost:8000/api/demo/presentation-stats
```

**Expected**: JSON with headline metrics, AI performance, testing efficiency, etc.

### Get Demo A/B Tests
```bash
curl http://localhost:8000/api/demo/ab-tests
```

**Expected**: JSON with 3 A/B tests showing Thompson Sampling results

### Reset Demo Data
```bash
curl -X POST http://localhost:8000/api/demo/reset
```

**Expected**:
```json
{
  "message": "Demo data reset successfully",
  "timestamp": "2024-12-05T..."
}
```

---

## 🎯 Test Checklist

### Backend Tests
- [ ] `/api/demo/status` returns 200
- [ ] `/api/demo/campaigns` returns demo campaigns
- [ ] `/api/demo/analytics` returns analytics data
- [ ] `/api/demo/ai-council` returns AI scores
- [ ] `/api/demo/ab-tests` returns A/B test data
- [ ] `/api/demo/presentation-stats` returns presentation stats
- [ ] `POST /api/demo/reset` clears data

### Frontend Tests
- [ ] `?demo=true` activates demo mode
- [ ] Demo badge appears in bottom-right
- [ ] Demo badge has exit button
- [ ] Demo badge has reset button (on hover)
- [ ] Dashboard shows demo data
- [ ] Analytics page shows demo charts
- [ ] Campaigns page shows demo campaigns

### Presentation Tests
- [ ] `/demo/presentation` loads without errors
- [ ] 7 slides render correctly
- [ ] Arrow keys navigate between slides
- [ ] `F` key toggles fullscreen
- [ ] `ESC` key exits presentation
- [ ] Slide indicators show current position
- [ ] All metrics display properly
- [ ] Charts and graphics render

---

## 🐛 Common Issues

### Issue: "Cannot GET /api/demo/status"

**Cause**: Gateway API not running or demo routes not loaded

**Fix**:
```bash
# Check if gateway-api is running
curl http://localhost:8000/health

# If not, start it
cd /home/user/geminivideo/services/gateway-api
npm run dev
```

### Issue: Demo badge not appearing

**Cause**: Frontend not detecting demo mode

**Fix**:
```javascript
// Open browser console
localStorage.setItem('demo_mode_enabled', 'true');
window.location.reload();
```

### Issue: 404 on presentation page

**Cause**: Route not registered in App.tsx

**Fix**: Verify `/demo/presentation` route exists in `App.tsx`. Should be there already.

### Issue: Keyboard shortcuts not working

**Cause**: Page not focused or input field is focused

**Fix**:
1. Click anywhere on the presentation
2. Make sure no input fields are focused
3. Try pressing arrow keys again

### Issue: Fullscreen not working

**Cause**: Browser security restrictions

**Fix**:
1. Make sure you clicked somewhere on the page first
2. Try pressing `F` key instead of button
3. Check browser console for errors

---

## 📊 Expected Demo Data

### Campaign Metrics
- **ROAS**: 2.5x - 3.8x
- **CTR**: 2.8% - 4.2%
- **Conversions**: 1,000 - 3,000
- **Spend**: €5,000 - €25,000
- **Revenue**: €15,000 - €80,000

### AI Council Scores
- **Overall Score**: 75 - 95
- **Approval Rate**: 85% - 95%
- **High Performers**: 60% - 80% of creatives

### A/B Test Results
- **Confidence**: 90% - 98%
- **Sample Size**: 50,000 - 150,000
- **Winner Improvement**: 30% - 60%

### Presentation Stats
- **Total Revenue**: €150,000 - €200,000
- **Active Campaigns**: 3 - 5
- **Average ROAS**: 3.0x - 3.5x
- **MoM Growth**: 20% - 30%

---

## 🎨 Visual Checks

### Dashboard
- [ ] Demo badge visible in bottom-right
- [ ] Badge has BeakerIcon
- [ ] Badge shows "Demo Mode" text
- [ ] Badge has exit button (X)
- [ ] Hover shows "Reset Data" button

### Presentation
- [ ] Gradient background changes per slide
- [ ] Icons render for each slide
- [ ] Metrics animate on load
- [ ] Charts are smooth
- [ ] Progress indicators work
- [ ] Navigation arrows functional
- [ ] Fullscreen button visible
- [ ] Exit button (X) visible

### Charts
- [ ] Daily metrics render
- [ ] Line charts smooth
- [ ] Bar charts visible
- [ ] Colors match theme (violet/purple)
- [ ] Tooltips work (if implemented)

---

## 🔄 Testing Scenarios

### Scenario 1: First-time Investor Demo
1. Open fresh browser (incognito)
2. Navigate to `/?demo=true`
3. Verify demo badge appears
4. Click "Analytics" in sidebar
5. Verify demo data shows
6. Navigate to `/demo/presentation`
7. Press `F` for fullscreen
8. Navigate through all 7 slides
9. Press `ESC` to exit
10. Verify you return to dashboard

### Scenario 2: Toggle Demo Mode
1. Start with demo mode off
2. Enable via badge or button
3. Verify data switches to demo
4. Disable demo mode
5. Verify data switches to real (or empty)

### Scenario 3: Reset Demo Data
1. Enable demo mode
2. Load campaigns page
3. Click demo badge
4. Hover to reveal "Reset Data"
5. Click "Reset Data"
6. Verify page reloads
7. Verify data is fresh

---

## 🎉 Success Criteria

### All tests pass when:
✅ Backend responds to all `/api/demo/*` endpoints
✅ Frontend shows demo badge when `?demo=true`
✅ Presentation page loads with 7 slides
✅ Keyboard shortcuts work as expected
✅ Fullscreen mode activates
✅ Data looks realistic and impressive
✅ No console errors
✅ Performance is smooth (<100ms API responses)

---

## 📞 Next Steps

After successful testing:

1. **Demo for Team**: Run through presentation with team
2. **Record Demo**: Record presentation for remote demos
3. **Prepare Investor Deck**: Take screenshots for pitch deck
4. **Schedule Investor Demos**: Start booking calls
5. **Track Metrics**: Monitor demo completion rates

---

## 🚀 Ready for Investors!

Once all tests pass, you're ready to present to investors with confidence.

**Good luck closing that €5M Series A!** 🎯

---

**Pro Tip**: Always test the presentation 30 minutes before an investor call to ensure everything works smoothly.
