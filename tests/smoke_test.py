import os
import json
import requests

BASE = os.environ.get("BASE_URL", "http://localhost:8080/v1/marketing")

def test_brief():
    r = requests.post(f"{BASE}/brief", json={"prompt":"Gen Z credit card launch: 'Financial freedom without the fees'."})
    r.raise_for_status()
    print(r.json())

if __name__ == "__main__":
    test_brief()
