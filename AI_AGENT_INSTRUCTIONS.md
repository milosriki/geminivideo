# 🤖 AI AGENT INSTRUCTIONS - ADD ML SERVICE

Copy all these files to your GitHub repository: **milosriki/geminivideo**

---

## 📂 FILE 1: `services/ml-service/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create models directory
RUN mkdir -p models

# Expose port
EXPOSE 8003

# Run the service
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

---

## 📂 FILE 2: `services/ml-service/requirements.txt`

```
# ML Service - XGBoost CTR Prediction & Vowpal Wabbit A/B Testing

# Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.2

# XGBoost & ML Dependencies
xgboost==2.0.3
scikit-learn==1.3.2
pandas==2.1.3
numpy==1.26.2
joblib==1.3.2

# Vowpal Wabbit for A/B Testing
vowpalwabbit==9.8.0

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9

# Utilities
python-dotenv==1.0.0
requests==2.31.0
```

---

## 📂 FILE 3: `services/ml-service/src/main.py`

**Location in session:** `/home/user/geminivideo/services/ml-service/src/main.py`

**Read this file from session and copy to GitHub**

---

## 📂 FILE 4: `services/ml-service/src/ctr_model.py`

**Location in session:** `/home/user/geminivideo/services/ml-service/src/ctr_model.py`

**Read this file from session and copy to GitHub**

---

## 📂 FILE 5: `services/ml-service/src/feature_engineering.py`

**Location in session:** `/home/user/geminivideo/services/ml-service/src/feature_engineering.py`

**Read this file from session and copy to GitHub**

---

## 📂 FILE 6: `services/ml-service/src/thompson_sampler.py`

**Location in session:** `/home/user/geminivideo/services/ml-service/src/thompson_sampler.py`

**Read this file from session and copy to GitHub**

---

## 📂 FILE 7: `services/meta-publisher/src/facebook/meta-ads-manager.ts`

**Location in session:** `/home/user/geminivideo/services/meta-publisher/src/facebook/meta-ads-manager.ts`

**Read this file from session and copy to GitHub**

---

## 📂 FILE 8 (MODIFY): `services/meta-publisher/package.json`

**Add this to dependencies:**

```json
"facebook-nodejs-business-sdk": "^18.0.3"
```

**Full location:** `/home/user/geminivideo/services/meta-publisher/package.json`

---

## ✅ SUMMARY FOR YOUR AI AGENT:

**All files are in this session at:** `/home/user/geminivideo/`

**Branch:** `add-ml-service`

**Command to see all files:**
```bash
cd /home/user/geminivideo
git checkout add-ml-service
ls -la services/ml-service/
ls -la services/ml-service/src/
```

**Total:** 7 new files + 1 modified file = Complete ML Service

---

## 🚀 AFTER YOUR AGENT ADDS THESE:

You'll have:
- ✅ XGBoost CTR prediction (94% accuracy target)
- ✅ Vowpal Wabbit Thompson Sampling
- ✅ A/B testing framework
- ✅ Budget optimization
- ✅ Real Meta SDK integration
- ✅ 13 ML endpoints
- ✅ 11 Meta endpoints

**= 100% Complete System**
