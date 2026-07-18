import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Alert:
    service: str
    severity: str
    incident: str
    timestamp: str

def save_alert(alert: Alert):
    # Ensure data directory exists
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    file_path = os.path.join(data_dir, 'incidents.json')
    
    incidents = []
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                incidents = json.load(f)
            except json.JSONDecodeError:
                pass
                
    incidents.append(asdict(alert))
    
    with open(file_path, 'w') as f:
        json.dump(incidents, f, indent=4)