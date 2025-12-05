# Alert System Quick Start Guide
**Agent 16 - Real-Time Performance Alerts**

---

## 5-Minute Quick Start

### 1. Start ML Service (Backend)
```bash
cd /home/user/geminivideo/services/ml-service
python -m uvicorn src.main:app --host 0.0.0.0 --port 8003 --reload
```

### 2. Start Gateway API (WebSocket + Proxy)
```bash
cd /home/user/geminivideo/services/gateway-api
npm install  # Install ws package
npm run dev
```

### 3. Start Frontend (Notifications Component)
```bash
cd /home/user/geminivideo/frontend
npm run dev
```

### 4. Test the System

#### Test Alert Trigger
```bash
curl -X POST http://localhost:8000/api/alerts/check \
  -H "Content-Type: application/json" \
  -d '{
    "metric_name": "roas",
    "metric_value": 1.5,
    "campaign_id": "test_campaign",
    "campaign_name": "Test Campaign"
  }'
```

#### View Active Alerts
```bash
curl http://localhost:8000/api/alerts
```

#### Test WebSocket Connection
```bash
# Install wscat
npm install -g wscat

# Connect to alert WebSocket
wscat -c ws://localhost:8000/ws/alerts
```

### 5. Add to Your Frontend

```typescript
// In your main layout or navbar component
import AlertNotifications from './components/AlertNotifications';

function Navbar() {
  return (
    <nav>
      {/* Other navbar items */}
      <AlertNotifications userId="current_user" />
    </nav>
  );
}
```

---

## Configuration

### Enable Email Notifications
```bash
# In .env or environment
export ALERT_EMAIL_ENABLED=true
export ALERT_EMAIL_RECIPIENTS=alerts@company.com
export ALERT_EMAIL_SMTP_HOST=smtp.gmail.com
export ALERT_EMAIL_SMTP_PORT=587
export ALERT_EMAIL_SENDER=alerts@company.com
export ALERT_EMAIL_PASSWORD=your_app_password
```

### Enable Slack Notifications
```bash
export ALERT_SLACK_ENABLED=true
export ALERT_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
export ALERT_SLACK_CHANNEL=#alerts
```

---

## Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/alerts/check` | POST | Check metric and trigger alerts |
| `/api/alerts` | GET | Get active alerts |
| `/api/alerts/{id}/acknowledge` | PUT | Acknowledge alert |
| `/api/alerts/{id}/resolve` | PUT | Resolve alert |
| `/api/alerts/rules` | GET | List alert rules |
| `/api/alerts/stats` | GET | Get statistics |
| `/ws/alerts` | WebSocket | Real-time alert stream |

---

## Default Alert Rules (Pre-configured)

1. **ROAS Drop < 2.0x** (HIGH) - 60min lookback, 30min cooldown
2. **ROAS Drop < 3.0x** (MEDIUM) - 2h lookback, 1h cooldown
3. **Budget 80% Spent** (MEDIUM) - 24h lookback, 6h cooldown
4. **Budget 100% Depleted** (CRITICAL) - 24h lookback, 12h cooldown
5. **Ad Disapproved** (CRITICAL) - 10min lookback, no cooldown
6. **CTR Drop >20%** (MEDIUM) - 1h lookback, 2h cooldown
7. **Conversion Spike >50%** (LOW) - 1h lookback, 2h cooldown
8. **Prediction Error >30%** (LOW) - 4h lookback, 6h cooldown
9. **CPA > $100** (HIGH) - 2h lookback, 1h cooldown
10. **Impressions < 1000/hour** (MEDIUM) - 1h lookback, 2h cooldown

---

## Testing

```bash
# Run end-to-end tests
cd /home/user/geminivideo/services/ml-service
python test_alert_system.py
```

Expected output:
```
✅ ALL TESTS PASSED!
Alert system is working correctly.
```

---

## Common Use Cases

### Monitor Campaign ROAS
```python
from src.alerts.alert_engine import alert_engine

# In your campaign monitoring loop
alerts = alert_engine.check_roas(
    campaign_id="camp_123",
    campaign_name="Black Friday Sale",
    roas=1.8,
    context={"spend": 5000, "revenue": 9000}
)
# Alerts automatically sent via configured channels
```

### Check Budget Usage
```python
spent_pct = (spent / daily_budget) * 100
alerts = alert_engine.check_budget(
    campaign_id="camp_123",
    campaign_name="Black Friday Sale",
    budget_spent_pct=spent_pct
)
```

### Create Custom Rule
```bash
curl -X POST http://localhost:8000/api/alerts/rules \
  -H "Content-Type: application/json" \
  -d '{
    "rule_id": "custom_roas_vip",
    "name": "VIP Campaign ROAS Alert",
    "alert_type": "roas_drop",
    "severity": "critical",
    "threshold": 5.0,
    "threshold_operator": "<",
    "lookback_minutes": 30,
    "cooldown_minutes": 15
  }'
```

---

## Troubleshooting

### WebSocket Not Connecting
- Check Gateway API is running on port 8000
- Verify `WS_URL` environment variable in frontend
- Check browser console for connection errors

### No Email Notifications
- Verify SMTP credentials are correct
- Check `ALERT_EMAIL_ENABLED=true`
- Test with: `curl -X POST http://localhost:8003/api/alerts/test?channel=email`

### Alerts Not Triggering
- Check metric values against rule thresholds
- Verify rules are enabled: `GET /api/alerts/rules`
- Check cooldown period hasn't been triggered recently

### Frontend Component Not Showing
- Verify API_URL is correct in frontend env
- Check network tab for API errors
- Ensure component is imported and rendered

---

## Production Deployment

### 1. Configure Notification Channels
```bash
# Set environment variables
ALERT_EMAIL_ENABLED=true
ALERT_SLACK_ENABLED=true
ALERT_WEBHOOK_ENABLED=true
```

### 2. Enable SSL for WebSocket
```nginx
# nginx.conf
location /ws/alerts {
    proxy_pass http://backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### 3. Set Up Monitoring
- Monitor WebSocket connection count
- Track alert trigger rate
- Set up alerts for alert system failures (meta!)

### 4. Database Integration
Replace in-memory storage with PostgreSQL:
```python
# In alert_engine.py, add database persistence
# Store active_alerts and alert_history in DB
```

---

## Support

For issues or questions:
1. Check logs: `docker logs ml-service`
2. Test endpoints with curl
3. Run test suite: `python test_alert_system.py`
4. Review documentation: `AGENT16_ALERTS_COMPLETE.md`

---

**Quick Start Complete!** 🚀

Your alert system is now monitoring campaigns 24/7 and will notify you immediately of any issues.
