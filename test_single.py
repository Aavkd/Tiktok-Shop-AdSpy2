import requests
import json

SERVICE_URL = "http://localhost:8081/signature"
TEST_URL = "https://www.tiktok.com/api/product/detail?productId=123456789"

resp = requests.post(SERVICE_URL, json={"url": TEST_URL})
print(json.dumps(resp.json(), indent=2))
