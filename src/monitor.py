import time
import json
import logging
import requests
import os
from datetime import datetime, timedelta

# Configuration
SIGNATURE_SERVICE_URL = "http://localhost:8081/signature"
MONITOR_LOG_FILE = "monitor_log.jsonl"
DEBUG_LOG_FILE = "debug_response.txt"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_signed_url(url):
    """
    Calls the local Node.js signature service to get X-Bogus/X-Gnarly.
    """
    try:
        response = requests.post(SIGNATURE_SERVICE_URL, json={"url": url})
        response.raise_for_status()
        json_resp = response.json()
        if json_resp.get("status") != "ok":
            logging.error(f"Signature service returned status: {json_resp.get('status')}")
            return None
        data = json_resp.get("data")
        return data
    except requests.exceptions.RequestException as e:
        logging.error(f"Error getting signature: {e}")
        return None

def fetch_product_data(product_url):
    """
    Fetches product data using signed requests.
    """
    logging.info(f"Fetching data for {product_url}...")
    
    # 1. Get signed URL and headers
    signed_data = get_signed_url(product_url)
    if not signed_data:
        logging.error("Failed to get signed URL.")
        return None

    signature_obj = signed_data.get("signed_url") # In my service, this is the signature object
    cookies = signed_data.get("cookies")
    user_agent = signed_data.get("navigator", {}).get("user_agent")
    
    # Construct the final URL with X-Bogus
    if isinstance(signature_obj, dict):
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        parsed = urlparse(product_url)
        query = parse_qs(parsed.query)
        
        # Add X-Bogus
        if "X-Bogus" in signature_obj:
            query["X-Bogus"] = signature_obj["X-Bogus"]
        if "X-Gnarly" in signature_obj:
            query["X-Gnarly"] = signature_obj["X-Gnarly"]
            
        new_query = urlencode(query, doseq=True)
        signed_url = urlunparse(parsed._replace(query=new_query))
    else:
        # Fallback if service returns full string (not current behavior but safe)
        signed_url = signature_obj if isinstance(signature_obj, str) else product_url

    headers = {
        "User-Agent": user_agent,
        "Cookie": cookies,
        "Referer": "https://www.tiktok.com/",
    }

    # 2. Make the request
    try:
        # Note: signed_url already contains X-Bogus and X-Gnarly as query params usually.
        # But if the service returns them separately, we might need to add them.
        # The README says signed_url has them.
        
        response = requests.get(signed_url, headers=headers)
        response.raise_for_status()
        
        # 3. Handle Response
        content_type = response.headers.get("Content-Type", "")
        
        # Debug save
        with open(DEBUG_LOG_FILE, "wb") as f:
            f.write(response.content)
            
        if "application/json" in content_type:
            try:
                data = response.json()
                return extract_product_info(data, product_url)
            except json.JSONDecodeError:
                logging.error("Failed to decode JSON response.")
                return None
        else:
            logging.warning(f"Response content type is {content_type}. Might be Protobuf.")
            # TODO: Add protobuf parsing if needed. For now, return None but log it.
            return None

    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {e}")
        return None

def extract_product_info(json_data, product_url):
    """
    Extracts relevant fields from the JSON response.
    This function needs to be adapted based on the actual response structure.
    """
    # Placeholder logic based on common TikTok structures
    # We will refine this once we see the actual JSON in debug_response.txt
    
    # Example structure (hypothetical):
    # {"data": {"product_info": {"stock": 100, "sold_count": 500, "price": {"min": 10, "max": 20}}}}
    
    try:
        # Navigate to product info (deep get)
        # This is highly dependent on the endpoint.
        # Assuming we hit a product detail endpoint.
        
        product_data = json_data.get("data", {})
        
        # If the response is empty or different, log it
        if not product_data:
            logging.warning("No 'data' field in JSON response.")
            return None

        # Extract fields
        item = product_data.get("product_info", {}) # Adjust key based on real response
        
        return {
            "timestamp": datetime.now().isoformat(),
            "url": product_url,
            "product_id": item.get("product_id", "unknown"),
            "total_stock": item.get("stock", 0),
            "total_sold": item.get("sold_count", 0),
            "price": item.get("price", {}).get("min_price", 0), # Simplified
            "raw_response_snippet": str(json_data)[:200] # For debugging
        }
    except Exception as e:
        logging.error(f"Error extracting product info: {e}")
        return None

def monitor_product(url, duration_days=7, interval_hours=1):
    start_time = datetime.now()
    end_time = start_time + timedelta(days=duration_days)
    
    logging.info(f"Starting monitor for: {url}")
    logging.info(f"Duration: {duration_days} days. Interval: {interval_hours} hours.")
    
    try:
        while datetime.now() < end_time:
            current_data = fetch_product_data(url)
            
            if current_data:
                # Save to file immediately
                with open(MONITOR_LOG_FILE, "a") as f:
                    f.write(json.dumps(current_data) + "\n")
                
                logging.info(f"Data recorded: {current_data}")
            else:
                logging.warning("No data fetched this interval.")
            
            # Sleep logic
            time.sleep(interval_hours * 3600)
            
    except KeyboardInterrupt:
        logging.info("Monitoring stopped manually.")
    
    logging.info("Monitoring finished.")

if __name__ == "__main__":
    # Example usage - Replace with a real URL or one from env/args
    # Using a placeholder for now
    target_url = "https://www.tiktok.com/@shop/product/example" 
    
    # Check if URL is passed as arg
    import sys
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
        
    # Set to very short interval for testing
    monitor_product(target_url, duration_days=7, interval_hours=1)
