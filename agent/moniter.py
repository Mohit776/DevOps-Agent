import time
import requests

def monitor_health():
    url = "http://localhost:3000/api/health"
    print(f"Starting health monitor for {url} (checking every 5 seconds)...")
    
    while True:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Healthy")
            else:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Generate Alert - Status Code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Generate Alert - Error: {e}")
            
        time.sleep(10)

if __name__ == "__main__":
    monitor_health()
