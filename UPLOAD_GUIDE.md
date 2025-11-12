# 📦 ALL ML SERVICE FILES - READY TO UPLOAD

**SIMPLEST METHOD:** Download these files and upload to GitHub

---

## 📁 File Structure

```
services/ml-service/
├── Dockerfile
├── requirements.txt
└── src/
    ├── main.py
    ├── ctr_model.py
    ├── feature_engineering.py
    └── thompson_sampler.py

services/meta-publisher/
├── package.json (UPDATE THIS)
└── src/facebook/
    └── meta-ads-manager.ts (NEW)
```

---

## ✅ OPTION 1: Use GitHub Desktop or Git

If you have access to clone the repo locally:

```bash
# Clone your repo
git clone https://github.com/milosriki/geminivideo.git
cd geminivideo

# The files are already in branch: add-ml-service
# Just push that branch:
git fetch
git checkout add-ml-service
git push origin add-ml-service
```

**Then go to GitHub and create a PR!**

---

## ✅ OPTION 2: Merge PR #19 First

**PR #19 already has 80% of the code.**

1. Go to: https://github.com/milosriki/geminivideo/pull/19
2. Click "Merge pull request"
3. Then only add the ML service (7 files)

---

## ✅ OPTION 3: I Create a GitHub Gist

I can create a public Gist with all files, then you:
1. Open the gist
2. Copy each file
3. Paste in GitHub web editor

**Want me to create the Gist?**

---

## 📝 All File Contents Below

(If you want to manually copy-paste, here's everything:)

### File 1: `services/ml-service/Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p models

EXPOSE 8003
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8003"]
```

### File 2: `services/ml-service/requirements.txt`
```
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.2
xgboost==2.0.3
scikit-learn==1.3.2
pandas==2.1.3
numpy==1.26.2
joblib==1.3.2
vowpalwabbit==9.8.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
python-dotenv==1.0.0
requests==2.31.0
```

### Files 3-7: Full source code at:
- `/home/user/geminivideo/services/ml-service/src/*.py`
- `/home/user/geminivideo/services/meta-publisher/src/facebook/meta-ads-manager.ts`

---

## 🎯 FASTEST WAY:

**Tell me which option you want:**

1. **"Merge PR #19"** - I'll tell you what to add after
2. **"Create Gist"** - I'll make a gist with all files
3. **"Show each file"** - I'll paste all files here (long)
4. **Something else** - Tell me what works

What do you prefer?
