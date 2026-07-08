import requests
import json

response = requests.post(
    "http://localhost:8000/api/chat", 
    json={"question": "What does [Occlusion] alarm mean?"}
)
print("Status:", response.status_code)
print("Body:", response.text)
