import os
import sys
import socket
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env_var(var_name):
    value = os.getenv(var_name)
    if value:
        print(f"✅ {var_name} is set")
        return True
    else:
        print(f"❌ {var_name} is MISSING")
        return False

def check_port(host, port, service_name):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((host, port))
        if result == 0:
            print(f"✅ {service_name} is listening on {host}:{port}")
            return True
        else:
            print(f"❌ {service_name} is NOT listening on {host}:{port}")
            return False
    except Exception as e:
        print(f"❌ {service_name} check failed: {e}")
        return False

def check_http_endpoint(url, service_name):
    try:
        response = requests.get(url, timeout=2)
        if response.status_code == 200:
            print(f"✅ {service_name} HTTP check passed ({url})")
            return True
        else:
            print(f"⚠️ {service_name} returned {response.status_code} (Expected 200)")
            return False
    except Exception as e:
        print(f"❌ {service_name} HTTP check failed: {e}")
        return False

def main():
    print("🚀 Starting Deployment Verification...\n")
    
    # 1. Environment Variables
    print("--- Environment Variables ---")
    env_ok = True
    env_ok &= check_env_var("GEMINI_API_KEY")
    env_ok &= check_env_var("DATABASE_URL")
    env_ok &= check_env_var("REDIS_URL")
    
    if not env_ok:
        print("\n⚠️  Some environment variables are missing. Check .env file.")
    else:
        print("\n✅ All critical environment variables are set.")

    # 2. Infrastructure
    print("\n--- Infrastructure ---")
    infra_ok = True
    infra_ok &= check_port("localhost", 5432, "PostgreSQL")
    infra_ok &= check_port("localhost", 6379, "Redis")
    
    # 3. Microservices (Port Checks)
    print("\n--- Microservices (Ports) ---")
    services_ok = True
    services_ok &= check_port("localhost", 8080, "Gateway API")
    services_ok &= check_port("localhost", 8081, "Drive Intel")
    services_ok &= check_port("localhost", 8082, "Video Agent")
    services_ok &= check_port("localhost", 8083, "Meta Publisher")
    services_ok &= check_port("localhost", 8084, "Titan Core")
    services_ok &= check_port("localhost", 8003, "ML Service")
    
    # 4. Service Health Checks (HTTP)
    print("\n--- Service Health Checks ---")
    health_ok = True
    # Assuming standard health endpoints or root returns 200/JSON
    health_ok &= check_http_endpoint("http://localhost:8080/health", "Gateway API")
    health_ok &= check_http_endpoint("http://localhost:8081/health", "Drive Intel")
    health_ok &= check_http_endpoint("http://localhost:8082/", "Video Agent")
    # Meta Publisher might not have a root endpoint documented, trying health if exists or root
    health_ok &= check_http_endpoint("http://localhost:8083/health", "Meta Publisher") 
    health_ok &= check_http_endpoint("http://localhost:8084/health", "Titan Core")
    health_ok &= check_http_endpoint("http://localhost:8003/health", "ML Service")

    print("\n--- Summary ---")
    if env_ok and infra_ok and services_ok and health_ok:
        print("✅✅✅ DEPLOYMENT READY! All systems go. ✅✅✅")
        sys.exit(0)
    else:
        print("⚠️  Deployment has issues. See logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
