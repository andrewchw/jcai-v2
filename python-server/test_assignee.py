import json

import requests

# Test the updated assignee functionality
url = "http://localhost:8000/api/chat/message/edge-1748270783635-lun5ucqg"
headers = {"Content-Type": "application/json"}
data = {
    "text": 'Create issues: Summary : "Test Assignee Lookup", Assignee : "Anson Chan", Due Date : "Friday"'
}

print("Testing assignee lookup with user display name...")
print(f"Request: {json.dumps(data, indent=2)}")
print()

try:
    response = requests.post(url, headers=headers, json=data, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
