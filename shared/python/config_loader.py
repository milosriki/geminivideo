"""
Shared config loader with GCS fallback
"""
import os
import json
import yaml
from typing import Any, Dict

def load_json_config(filename: str, default: Dict = None) -> Dict[str, Any]:
    """Load JSON config from local path or GCS"""
    config_path = os.getenv("CONFIG_PATH", "/app/config")
    gcs_bucket = os.getenv("GCS_BUCKET", "")

    # Try local first
    local_path = f"{config_path}/{filename}"
    try:
        with open(local_path, "r") as f:
            config = json.load(f)
            print(f"✅ Loaded {filename} from {local_path}")
            return config
    except FileNotFoundError:
        print(f"⚠️  {filename} not found at {local_path}")

    # Try GCS if bucket configured
    if gcs_bucket:
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(gcs_bucket)
            blob = bucket.blob(f"config/{filename}")
            config = json.loads(blob.download_as_string())
            print(f"✅ Loaded {filename} from gs://{gcs_bucket}/config/{filename}")
            return config
        except Exception as e:
            print(f"⚠️  Failed to load {filename} from GCS: {e}")

    # Return default if provided
    if default is not None:
        print(f"⚠️  Using default config for {filename}")
        return default

    # Raise error if no default
    raise FileNotFoundError(f"Config file {filename} not found in local or GCS")

def load_yaml_config(filename: str, default: Dict = None) -> Dict[str, Any]:
    """Load YAML config from local path or GCS"""
    config_path = os.getenv("CONFIG_PATH", "/app/config")
    gcs_bucket = os.getenv("GCS_BUCKET", "")

    # Try local first
    local_path = f"{config_path}/{filename}"
    try:
        with open(local_path, "r") as f:
            config = yaml.safe_load(f)
            print(f"✅ Loaded {filename} from {local_path}")
            return config
    except FileNotFoundError:
        print(f"⚠️  {filename} not found at {local_path}")

    # Try GCS if bucket configured
    if gcs_bucket:
        try:
            from google.cloud import storage
            client = storage.Client()
            bucket = client.bucket(gcs_bucket)
            blob = bucket.blob(f"config/{filename}")
            config = yaml.safe_load(blob.download_as_string())
            print(f"✅ Loaded {filename} from gs://{gcs_bucket}/config/{filename}")
            return config
        except Exception as e:
            print(f"⚠️  Failed to load {filename} from GCS: {e}")

    # Return default if provided
    if default is not None:
        print(f"⚠️  Using default config for {filename}")
        return default

    # Raise error if no default
    raise FileNotFoundError(f"Config file {filename} not found in local or GCS")
