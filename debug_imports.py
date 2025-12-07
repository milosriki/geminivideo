import sys
print(f"Python version: {sys.version}")
print(f"Path: {sys.path}")

try:
    import fastapi
    print("fastapi: OK")
except ImportError as e:
    print(f"fastapi: FAILED - {e}")

try:
    import uvicorn
    print("uvicorn: OK")
except ImportError as e:
    print(f"uvicorn: FAILED - {e}")

try:
    import pydantic
    print("pydantic: OK")
except ImportError as e:
    print(f"pydantic: FAILED - {e}")

try:
    import pandas
    print("pandas: OK")
except ImportError as e:
    print(f"pandas: FAILED - {e}")

try:
    import numpy
    print("numpy: OK")
except ImportError as e:
    print(f"numpy: FAILED - {e}")

try:
    import sklearn
    print("sklearn: OK")
except ImportError as e:
    print(f"sklearn: FAILED - {e}")

try:
    import xgboost
    print("xgboost: OK")
except ImportError as e:
    print(f"xgboost: FAILED - {e}")

try:
    import sqlalchemy
    print("sqlalchemy: OK")
except ImportError as e:
    print(f"sqlalchemy: FAILED - {e}")

try:
    import asyncpg
    print("asyncpg: OK")
except ImportError as e:
    print(f"asyncpg: FAILED - {e}")

try:
    import psycopg2
    print("psycopg2: OK")
except ImportError as e:
    print(f"psycopg2: FAILED - {e}")

try:
    import httpx
    print("httpx: OK")
except ImportError as e:
    print(f"httpx: FAILED - {e}")
