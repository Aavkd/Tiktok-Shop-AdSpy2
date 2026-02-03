import sys
import os
import time
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from monitor import fetch_product_data, monitor_product

# Test fetch_product_data directly
url = "https://www.tiktok.com/@shop/product/example"

print(f"Testing fetch_product_data directly for {url}...")
try:
    data = fetch_product_data(url)
    if data:
        print("SUCCESS: Data fetched:")
        print(data)
    else:
        print("FAILED: fetch_product_data returned None (This might be expected for dummy URL if scraper logic fails on content)")
        # Since I am using a dummy URL, it will likely fail to extract product info
        # but fetching should succeed (status 200).
        # Let's check if the raw response was saved.
        if os.path.exists("debug_response.txt"):
             print("SUCCESS: debug_response.txt created.")
        else:
             print("FAILED: debug_response.txt not created.")
except Exception as e:
    print(f"ERROR: {e}")

# If needed, test full monitor loop for a few seconds
# But direct fetch is enough for E2E verification of the signature + request flow.
