# 🔧 Fix for Python 3.14 Compatibility Issue

## Problem
Python 3.14 is too new - `jsonschema-rs` (required by `langgraph-api`) doesn't support it yet.

## ✅ Solution: Install Python 3.13

### Option 1: Download Python 3.13 (Recommended) ⭐

**Important:** Python 3.11.14 has NO binary installers (source-only). Use Python 3.13 instead.

1. **Download Python 3.13:**
   - Go to: https://www.python.org/downloads/
   - Click "Download Python 3.13.x" (latest 3.13 version)
   - Or go directly to: https://www.python.org/downloads/release/python-31311/
   - Download: "macOS 64-bit universal2 installer" (works on both Intel and Apple Silicon)
   - Run the installer

2. **Verify installation:**
   ```bash
   /usr/local/bin/python3.13 --version
   # Should show: Python 3.13.0
   ```

3. **Install langgraph-cli with Python 3.13:**
   ```bash
   /usr/local/bin/python3.13 -m pip install -U "langgraph-cli[inmem]"
   ```

4. **Use Python 3.13 for langgraph:**
   ```bash
   /usr/local/bin/python3.13 -m langgraph dev
   ```

### Option 2: Use System Python 3.9 (May not work - requires Python 3.10+)

Try this if you can't install Python 3.13:

```bash
/usr/bin/python3 -m pip install -U "langgraph-cli[inmem]"
/usr/bin/python3 -m langgraph dev
```

**Note:** This may fail because the project requires Python 3.10+.

### Option 3: Use Docker (Alternative)

If you have Docker installed:

```bash
# Create a Dockerfile
cat > Dockerfile << 'EOF'
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install -U "langgraph-cli[inmem]"
CMD ["langgraph", "dev", "--host", "0.0.0.0"]
EOF

# Build and run
docker build -t langgraph-app .
docker run -p 2024:2024 langgraph-app
```

---

## Quick Fix Commands

After installing Python 3.13:

```bash
# Navigate to project
cd /Users/milosvukovic/geminivideo/services/langgraph-app

# Install with Python 3.13
/usr/local/bin/python3.13 -m pip install -U "langgraph-cli[inmem]"

# Start server with Python 3.13
/usr/local/bin/python3.13 -m langgraph dev
```

---

## Why This Happens

- Python 3.14 was just released (October 2024)
- `jsonschema-rs` uses Rust bindings that don't support Python 3.14 yet
- Python 3.13 is the latest stable version that works
- **Note:** Python 3.11.14 has no binary installers (source-only) - not recommended

---

## After Fixing

Once the server starts, you'll see:
```
>    Ready!
>    - API: http://localhost:2024
>    - LangSmith Studio Web UI: https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024
```

Then connect in LangSmith Studio with Base URL: `http://localhost:2024`

