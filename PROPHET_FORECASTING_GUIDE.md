# 📈 Prophet Forecasting: How to Use It in GeminiVideo

**Generated:** 2025-01-08  
**Purpose:** Guide to adding and using Facebook Prophet for time series forecasting

**What is Prophet?**
- Facebook's open-source time series forecasting library
- Handles seasonality, trends, and holidays automatically
- Perfect for predicting ad performance trends

---

## 🎯 WHERE TO USE PROPHET

### 1. **ROAS Trend Forecasting**
Predict future ROAS based on historical performance

### 2. **CTR Trend Forecasting**
Forecast click-through rates over time

### 3. **Budget Forecasting**
Predict optimal budgets for future periods

### 4. **Seasonal Pattern Detection**
Identify weekly/monthly patterns automatically

### 5. **Performance Anomaly Detection**
Detect when performance deviates from expected trends

---

## 📦 INSTALLATION

### Step 1: Add to Requirements

```bash
# services/ml-service/requirements.txt
prophet==1.1.5
```

### Step 2: Install

```bash
cd services/ml-service
pip install prophet==1.1.5
```

**Note:** Prophet requires `pystan` which can be tricky. Use conda if possible:
```bash
conda install -c conda-forge prophet
```

---

## 🚀 IMPLEMENTATION

### Option 1: Create New Prophet Service

Create `services/ml-service/src/prophet_forecaster.py`:

```python
"""
Prophet Time Series Forecasting
Predicts future ad performance trends
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import pandas as pd
from prophet import Prophet
import numpy as np

logger = logging.getLogger(__name__)


class ProphetForecaster:
    """
    Uses Facebook Prophet for time series forecasting.
    
    Perfect for:
    - ROAS trend prediction
    - CTR forecasting
    - Budget optimization
    - Seasonal pattern detection
    """
    
    def __init__(self):
        self.models = {}  # Cache models per metric/campaign
    
    def forecast_roas(
        self,
        historical_data: List[Dict],
        days_ahead: int = 7,
        include_uncertainty: bool = True
    ) -> Dict[str, Any]:
        """
        Forecast ROAS for next N days.
        
        Args:
            historical_data: List of {date, roas} dicts
            days_ahead: Days to forecast
            include_uncertainty: Include confidence intervals
        
        Returns:
            Forecast dict with predictions and confidence intervals
        """
        # Prepare data for Prophet
        df = pd.DataFrame(historical_data)
        df['ds'] = pd.to_datetime(df['date'])
        df['y'] = df['roas']
        df = df[['ds', 'y']].sort_values('ds')
        
        # Create and fit model
        model = Prophet(
            yearly_seasonality=True,  # Annual patterns
            weekly_seasonality=True,   # Weekly patterns
            daily_seasonality=False,   # Usually not needed for daily data
            changepoint_prior_scale=0.05,  # Flexibility for trend changes
            seasonality_mode='multiplicative'  # Multiplicative seasonality
        )
        
        # Add custom seasonalities if needed
        # model.add_seasonality(name='monthly', period=30.5, fourier_order=5)
        
        model.fit(df)
        
        # Create future dataframe
        future = model.make_future_dataframe(periods=days_ahead)
        
        # Forecast
        forecast = model.predict(future)
        
        # Extract forecast period only
        forecast_period = forecast.tail(days_ahead)
        
        # Format results
        predictions = []
        for _, row in forecast_period.iterrows():
            pred = {
                'date': row['ds'].isoformat(),
                'predicted_roas': round(row['yhat'], 4),
                'lower_bound': round(row['yhat_lower'], 4) if include_uncertainty else None,
                'upper_bound': round(row['yhat_upper'], 4) if include_uncertainty else None,
            }
            predictions.append(pred)
        
        # Calculate trend
        trend = self._calculate_trend(forecast_period)
        
        # Detect seasonality
        seasonality = self._detect_seasonality(model, forecast_period)
        
        return {
            'metric': 'roas',
            'forecast_days': days_ahead,
            'predictions': predictions,
            'trend': trend,
            'seasonality': seasonality,
            'model_components': {
                'trend': forecast_period['trend'].tolist(),
                'weekly': forecast_period['weekly'].tolist() if 'weekly' in forecast_period.columns else None,
                'yearly': forecast_period['yearly'].tolist() if 'yearly' in forecast_period.columns else None,
            }
        }
    
    def forecast_ctr(
        self,
        historical_data: List[Dict],
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Forecast CTR for next N days.
        """
        df = pd.DataFrame(historical_data)
        df['ds'] = pd.to_datetime(df['date'])
        df['y'] = df['ctr']
        df = df[['ds', 'y']].sort_values('ds')
        
        model = Prophet(
            yearly_seasonality=True,
            weekly_seasonality=True,
            changepoint_prior_scale=0.05
        )
        model.fit(df)
        
        future = model.make_future_dataframe(periods=days_ahead)
        forecast = model.predict(future)
        
        forecast_period = forecast.tail(days_ahead)
        
        predictions = []
        for _, row in forecast_period.iterrows():
            predictions.append({
                'date': row['ds'].isoformat(),
                'predicted_ctr': round(row['yhat'], 6),
                'lower_bound': round(row['yhat_lower'], 6),
                'upper_bound': round(row['yhat_upper'], 6),
            })
        
        return {
            'metric': 'ctr',
            'forecast_days': days_ahead,
            'predictions': predictions,
            'trend': self._calculate_trend(forecast_period)
        }
    
    def forecast_budget_optimization(
        self,
        campaign_id: str,
        historical_data: List[Dict],
        target_roas: float = 3.0,
        days_ahead: int = 7
    ) -> Dict[str, Any]:
        """
        Forecast optimal budget allocation based on predicted ROAS.
        
        Uses Prophet to predict ROAS, then recommends budget changes.
        """
        # Forecast ROAS
        roas_forecast = self.forecast_roas(historical_data, days_ahead)
        
        # Calculate budget recommendations
        recommendations = []
        for pred in roas_forecast['predictions']:
            predicted_roas = pred['predicted_roas']
            
            # If predicted ROAS > target, recommend increase
            if predicted_roas > target_roas * 1.1:  # 10% above target
                recommendation = 'increase'
                multiplier = min(1.5, predicted_roas / target_roas)  # Cap at 1.5x
            elif predicted_roas < target_roas * 0.9:  # 10% below target
                recommendation = 'decrease'
                multiplier = max(0.5, predicted_roas / target_roas)  # Floor at 0.5x
            else:
                recommendation = 'maintain'
                multiplier = 1.0
            
            recommendations.append({
                'date': pred['date'],
                'predicted_roas': predicted_roas,
                'recommendation': recommendation,
                'budget_multiplier': round(multiplier, 2),
                'confidence': self._calculate_confidence(pred)
            })
        
        return {
            'campaign_id': campaign_id,
            'target_roas': target_roas,
            'forecast_days': days_ahead,
            'recommendations': recommendations,
            'summary': {
                'avg_predicted_roas': np.mean([r['predicted_roas'] for r in recommendations]),
                'increase_days': len([r for r in recommendations if r['recommendation'] == 'increase']),
                'decrease_days': len([r for r in recommendations if r['recommendation'] == 'decrease']),
                'maintain_days': len([r for r in recommendations if r['recommendation'] == 'maintain']),
            }
        }
    
    def detect_anomalies(
        self,
        historical_data: List[Dict],
        recent_data: List[Dict]
    ) -> Dict[str, Any]:
        """
        Detect performance anomalies using Prophet.
        
        Compares recent performance to Prophet's forecast.
        """
        # Forecast based on historical data
        forecast = self.forecast_roas(historical_data, days_ahead=len(recent_data))
        
        # Compare recent data to forecast
        anomalies = []
        for i, recent_point in enumerate(recent_data):
            forecast_point = forecast['predictions'][i]
            
            actual_roas = recent_point['roas']
            predicted_roas = forecast_point['predicted_roas']
            lower_bound = forecast_point['lower_bound']
            upper_bound = forecast_point['upper_bound']
            
            # Check if outside confidence interval
            is_anomaly = actual_roas < lower_bound or actual_roas > upper_bound
            
            if is_anomaly:
                deviation = ((actual_roas - predicted_roas) / predicted_roas) * 100
                
                anomalies.append({
                    'date': recent_point['date'],
                    'actual_roas': actual_roas,
                    'predicted_roas': predicted_roas,
                    'deviation_pct': round(deviation, 2),
                    'severity': 'high' if abs(deviation) > 30 else 'medium',
                    'direction': 'above' if deviation > 0 else 'below'
                })
        
        return {
            'anomalies_detected': len(anomalies),
            'anomalies': anomalies,
            'total_points_checked': len(recent_data)
        }
    
    def _calculate_trend(self, forecast: pd.DataFrame) -> Dict[str, Any]:
        """Calculate trend direction and strength"""
        trend_values = forecast['trend'].values
        first_value = trend_values[0]
        last_value = trend_values[-1]
        
        change_pct = ((last_value - first_value) / first_value) * 100
        
        return {
            'direction': 'increasing' if change_pct > 0 else 'decreasing',
            'change_pct': round(change_pct, 2),
            'strength': 'strong' if abs(change_pct) > 10 else 'moderate' if abs(change_pct) > 5 else 'weak'
        }
    
    def _detect_seasonality(self, model: Prophet, forecast: pd.DataFrame) -> Dict[str, Any]:
        """Detect seasonal patterns"""
        seasonality = {}
        
        if 'weekly' in forecast.columns:
            weekly_values = forecast['weekly'].values
            seasonality['weekly'] = {
                'amplitude': round(np.max(weekly_values) - np.min(weekly_values), 4),
                'pattern': 'detected' if np.std(weekly_values) > 0.01 else 'none'
            }
        
        if 'yearly' in forecast.columns:
            yearly_values = forecast['yearly'].values
            seasonality['yearly'] = {
                'amplitude': round(np.max(yearly_values) - np.min(yearly_values), 4),
                'pattern': 'detected' if np.std(yearly_values) > 0.01 else 'none'
            }
        
        return seasonality
    
    def _calculate_confidence(self, prediction: Dict) -> float:
        """Calculate confidence score based on uncertainty interval"""
        if not prediction.get('lower_bound') or not prediction.get('upper_bound'):
            return 0.5  # Default if no uncertainty
        
        interval_width = prediction['upper_bound'] - prediction['lower_bound']
        predicted_value = prediction['predicted_roas']
        
        # Narrower interval = higher confidence
        relative_width = interval_width / predicted_value if predicted_value > 0 else 1.0
        
        # Convert to 0-1 confidence score
        confidence = max(0.0, min(1.0, 1.0 - relative_width))
        
        return round(confidence, 2)


# Singleton instance
_prophet_forecaster = None

def get_prophet_forecaster() -> ProphetForecaster:
    """Get singleton Prophet forecaster instance"""
    global _prophet_forecaster
    if _prophet_forecaster is None:
        _prophet_forecaster = ProphetForecaster()
    return _prophet_forecaster
```

---

## 🔌 WIRING TO API

Add endpoints to `services/ml-service/src/main.py`:

```python
# Add import
from src.prophet_forecaster import get_prophet_forecaster

# Add endpoints
@app.post("/api/ml/prophet/forecast-roas", tags=["Prophet Forecasting"])
async def forecast_roas(request: Dict[str, Any]):
    """
    Forecast ROAS for next N days using Prophet.
    
    Request:
    {
        "historical_data": [
            {"date": "2025-01-01", "roas": 3.2},
            {"date": "2025-01-02", "roas": 3.5},
            ...
        ],
        "days_ahead": 7
    }
    """
    try:
        forecaster = get_prophet_forecaster()
        result = forecaster.forecast_roas(
            historical_data=request['historical_data'],
            days_ahead=request.get('days_ahead', 7)
        )
        return result
    except Exception as e:
        logger.error(f"Error forecasting ROAS: {e}", exc_info=True)
        raise HTTPException(500, str(e))

@app.post("/api/ml/prophet/forecast-ctr", tags=["Prophet Forecasting"])
async def forecast_ctr(request: Dict[str, Any]):
    """Forecast CTR using Prophet"""
    try:
        forecaster = get_prophet_forecaster()
        result = forecaster.forecast_ctr(
            historical_data=request['historical_data'],
            days_ahead=request.get('days_ahead', 7)
        )
        return result
    except Exception as e:
        logger.error(f"Error forecasting CTR: {e}", exc_info=True)
        raise HTTPException(500, str(e))

@app.post("/api/ml/prophet/budget-optimization", tags=["Prophet Forecasting"])
async def forecast_budget_optimization(request: Dict[str, Any]):
    """Forecast optimal budget allocation"""
    try:
        forecaster = get_prophet_forecaster()
        result = forecaster.forecast_budget_optimization(
            campaign_id=request['campaign_id'],
            historical_data=request['historical_data'],
            target_roas=request.get('target_roas', 3.0),
            days_ahead=request.get('days_ahead', 7)
        )
        return result
    except Exception as e:
        logger.error(f"Error forecasting budget: {e}", exc_info=True)
        raise HTTPException(500, str(e))

@app.post("/api/ml/prophet/detect-anomalies", tags=["Prophet Forecasting"])
async def detect_anomalies(request: Dict[str, Any]):
    """Detect performance anomalies using Prophet"""
    try:
        forecaster = get_prophet_forecaster()
        result = forecaster.detect_anomalies(
            historical_data=request['historical_data'],
            recent_data=request['recent_data']
        )
        return result
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}", exc_info=True)
        raise HTTPException(500, str(e))
```

---

## 📊 USAGE EXAMPLES

### Example 1: Forecast ROAS

```python
import requests

# Get historical ROAS data
historical_data = [
    {"date": "2025-01-01", "roas": 3.2},
    {"date": "2025-01-02", "roas": 3.5},
    {"date": "2025-01-03", "roas": 3.1},
    # ... more data
]

# Forecast next 7 days
response = requests.post(
    "http://localhost:8003/api/ml/prophet/forecast-roas",
    json={
        "historical_data": historical_data,
        "days_ahead": 7
    }
)

result = response.json()
# {
#   "metric": "roas",
#   "forecast_days": 7,
#   "predictions": [
#     {
#       "date": "2025-01-08T00:00:00",
#       "predicted_roas": 3.4,
#       "lower_bound": 2.8,
#       "upper_bound": 4.0
#     },
#     ...
#   ],
#   "trend": {
#     "direction": "increasing",
#     "change_pct": 5.2,
#     "strength": "moderate"
#   }
# }
```

### Example 2: Budget Optimization

```python
# Forecast optimal budget based on predicted ROAS
response = requests.post(
    "http://localhost:8003/api/ml/prophet/budget-optimization",
    json={
        "campaign_id": "campaign-123",
        "historical_data": historical_data,
        "target_roas": 3.0,
        "days_ahead": 7
    }
)

result = response.json()
# {
#   "campaign_id": "campaign-123",
#   "target_roas": 3.0,
#   "recommendations": [
#     {
#       "date": "2025-01-08",
#       "predicted_roas": 3.4,
#       "recommendation": "increase",
#       "budget_multiplier": 1.13,
#       "confidence": 0.85
#     },
#     ...
#   ]
# }
```

### Example 3: Anomaly Detection

```python
# Detect if recent performance is anomalous
response = requests.post(
    "http://localhost:8003/api/ml/prophet/detect-anomalies",
    json={
        "historical_data": historical_data,
        "recent_data": [
            {"date": "2025-01-08", "roas": 1.5},  # Much lower than predicted
            {"date": "2025-01-09", "roas": 1.3}
        ]
    }
)

result = response.json()
# {
#   "anomalies_detected": 2,
#   "anomalies": [
#     {
#       "date": "2025-01-08",
#       "actual_roas": 1.5,
#       "predicted_roas": 3.4,
#       "deviation_pct": -55.88,
#       "severity": "high",
#       "direction": "below"
#     }
#   ]
# }
```

---

## 🔗 INTEGRATION WITH EXISTING SYSTEMS

### 1. **Integrate with BattleHardenedSampler**

```python
# services/ml-service/src/battle_hardened_sampler.py

from src.prophet_forecaster import get_prophet_forecaster

class BattleHardenedSampler:
    def select_budget_allocation(self, ad_states, total_budget, creative_dna_scores=None):
        # ... existing logic ...
        
        # Add Prophet forecast boost
        forecaster = get_prophet_forecaster()
        for ad in ad_states:
            # Get historical ROAS for this ad
            historical = self._get_historical_roas(ad.ad_id)
            
            if len(historical) >= 30:  # Need enough data
                forecast = forecaster.forecast_roas(historical, days_ahead=1)
                predicted_roas = forecast['predictions'][0]['predicted_roas']
                
                # Boost ads with positive forecast
                if predicted_roas > ad.pipeline_roas * 1.1:
                    # Increase budget allocation
                    ...
```

### 2. **Integrate with Oracle Agent**

```python
# services/titan-core/ai_council/oracle_agent.py

from ml_service.src.prophet_forecaster import get_prophet_forecaster

class OracleAgent:
    def predict_performance(self, creative_id, creative_features):
        # ... existing prediction ...
        
        # Add Prophet trend analysis
        forecaster = get_prophet_forecaster()
        historical = self._get_account_historical_performance()
        
        if len(historical) >= 30:
            forecast = forecaster.forecast_roas(historical, days_ahead=7)
            trend = forecast['trend']
            
            # Adjust prediction based on trend
            if trend['direction'] == 'increasing':
                predicted_roas *= 1.1  # Boost for upward trend
            elif trend['direction'] == 'decreasing':
                predicted_roas *= 0.9  # Reduce for downward trend
        
        return predicted_roas
```

### 3. **Integrate with Time Optimizer**

```python
# services/ml-service/src/time_optimizer.py

from src.prophet_forecaster import get_prophet_forecaster

class TimeBasedOptimizer:
    def recommend_budget_schedule(self, campaign_id, base_daily_budget, peak_multiplier=1.3):
        # ... existing logic ...
        
        # Add Prophet forecast for each hour
        forecaster = get_prophet_forecaster()
        historical = self._get_hourly_historical_data(campaign_id)
        
        if len(historical) >= 168:  # 7 days of hourly data
            forecast = forecaster.forecast_roas(historical, days_ahead=1)
            
            # Adjust schedule based on forecast
            for hour_schedule in schedule:
                hour = hour_schedule['hour']
                predicted_roas = forecast['predictions'][hour]['predicted_roas']
                
                # Boost hours with high predicted ROAS
                if predicted_roas > target_roas:
                    hour_schedule['budget'] *= 1.2
        
        return schedule
```

---

## 📈 BENEFITS

1. **Automatic Seasonality Detection**
   - Prophet automatically detects weekly/monthly patterns
   - No manual feature engineering needed

2. **Uncertainty Intervals**
   - Provides confidence bounds for predictions
   - Helps with risk assessment

3. **Trend Detection**
   - Identifies increasing/decreasing trends
   - Adjusts predictions accordingly

4. **Anomaly Detection**
   - Flags when performance deviates from expected
   - Early warning system

5. **Budget Optimization**
   - Predicts optimal budget allocation
   - Based on forecasted performance

---

## 🚀 NEXT STEPS

1. **Install Prophet** ✅
   ```bash
   pip install prophet==1.1.5
   ```

2. **Create Prophet Service** ✅
   - Copy code from above
   - Save to `services/ml-service/src/prophet_forecaster.py`

3. **Wire to API** ✅
   - Add endpoints to `main.py`

4. **Integrate with Existing Systems** ✅
   - BattleHardenedSampler
   - Oracle Agent
   - Time Optimizer

5. **Test** ✅
   - Use historical data to validate forecasts
   - Compare Prophet predictions to actuals

---

## 📚 REFERENCES

- [Prophet Documentation](https://facebook.github.io/prophet/)
- [Prophet GitHub](https://github.com/facebook/prophet)
- [Prophet Paper](https://peerj.com/preprints/3190/)

---

**Key Insight:** Prophet is perfect for GeminiVideo because it handles seasonality automatically (weekly patterns, monthly trends) and provides uncertainty intervals for risk-aware decision making. It's battle-tested at Facebook scale and perfect for ad performance forecasting.

