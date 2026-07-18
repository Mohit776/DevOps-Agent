import time
import requests
from datetime import datetime
from dataclasses import asdict
from alert import Alert, save_alert
from graph import run_agent

def monitor_health():
    url = "http://localhost:3000/api/health"
    print(f"Starting health monitor for {url} (checking every 10 seconds)...")
    
    while True:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Healthy")
            else:
                print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Generate Alert - Status Code: {response.status_code}")
                alert = Alert(
                    service="app",
                    severity="HIGH",
                    incident=f"Service returned status {response.status_code}",
                    timestamp=datetime.now().isoformat()
                )
                save_alert(alert)
                run_agent(asdict(alert))
                
        except requests.exceptions.RequestException as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Generate Alert - Error: {e}")
            alert = Alert(
                service="app",
                severity="CRITICAL",
                incident=str(e),
                timestamp=datetime.now().isoformat()
            )
            save_alert(alert)
            run_agent(asdict(alert))
            
        time.sleep(5)

if __name__ == "__main__":
    monitor_health()
