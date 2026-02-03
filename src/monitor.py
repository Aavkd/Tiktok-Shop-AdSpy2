import os
import sys
import json
import logging
import time
import requests
from curl_cffi import requests as cffi_requests
import asyncio
import re
from datetime import datetime, timedelta

# Try importing Apify Actor SDK
try:
    from apify import Actor
except ImportError:
    Actor = None

# Configuration
SIGNATURE_SERVICE_URL = "http://localhost:8081/signature"
MONITOR_LOG_FILE = "monitor_log.jsonl"
DEBUG_LOG_FILE = "debug_response.txt"

# Configure logging
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
    except Exception as e:
        logging.error(f"Error calling signature service: {e}")
        return None

def parse_html_for_data(html_content, product_url):
    """
    Parses HTML content to find embedded JSON data (SIGI_STATE, __UNIVERSAL_DATA, etc.).
    """
    logging.info("Parsing HTML for embedded data...")
    
    # List of patterns to look for
    patterns = [
        r'<script id="SIGI_STATE" type="application/json">(.*?)</script>',
        r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>',
        r'window\[\'SIGI_STATE\'\]\s*=\s*({.*?});',
        r'window\.__UNIVERSAL_DATA_FOR_REHYDRATION__\s*=\s*({.*?});'
    ]
    
    json_data = None
    
    for pattern in patterns:
        match = re.search(pattern, html_content, re.DOTALL)
        if match:
            try:
                json_str = match.group(1)
                json_data = json.loads(json_str)
                logging.info(f"Found JSON data using pattern: {pattern[:20]}...")
                break
            except json.JSONDecodeError as e:
                logging.warning(f"Found match but failed to decode JSON: {e}")
                continue
                
    if not json_data:
        logging.warning("No JSON data found in HTML.")
        # Attempt fallback: Look for "ItemModule" or similar direct structures if full hydration failed
        return None

    # Extraction Logic
    # The structure varies. We need to find the Product info.
    try:
        # Common paths in SIGI_STATE / Universal Data
        # 1. ItemModule -> <id>
        # 2. ProductDetail -> ...
        # 3. 'webapp.video-detail' -> ...
        
        product_info = {}
        
        # Helper to find product data in nested dicts
        # We look for "stock" and "price" keys
        
        # Strategy: Flatten or search? 
        # Let's try known paths first.
        
        item_data = None
        
        if "ItemModule" in json_data:
            # Usually keyed by video ID or product ID
            for key, val in json_data["ItemModule"].items():
                if val and ("price" in val or "stock" in val):
                    item_data = val
                    break
                    
        if not item_data and "ProductDetail" in json_data:
             item_data = json_data.get("ProductDetail")

        # Universal Data structure (e.g. from __UNIVERSAL_DATA__)
        if not item_data and "__DEFAULT_SCOPE__" in json_data:
             scope = json_data["__DEFAULT_SCOPE__"]
             if "webapp.product-detail" in scope:
                 item_data = scope["webapp.product-detail"].get("productInfo")
        
        if item_data:
            return {
                "timestamp": datetime.now().isoformat(),
                "url": product_url,
                "product_id": item_data.get("id") or item_data.get("product_id") or "unknown",
                "title": item_data.get("title") or item_data.get("name"),
                "total_stock": item_data.get("stock", 0) or item_data.get("quantity", 0),
                "total_sold": item_data.get("sold_count", 0) or item_data.get("sales", 0),
                "price": item_data.get("price", {}).get("min_price") or item_data.get("price", 0),
                "currency": item_data.get("price", {}).get("currency") or "USD",
                "status": "active" if item_data.get("status") == 1 else "inactive",
                "raw_response_snippet": "HTML Parsing Success"
            }
            
        logging.warning("JSON found but could not locate specific Product Info inside.")
        return None

    except Exception as e:
        logging.error(f"Error extracting data from JSON: {e}")
        return None

def fetch_product_data(product_url):
    """
    Fetches product data using signed requests and curl_cffi for TLS impersonation.
    """
    logging.info(f"Fetching data for {product_url}...")
    
    # 1. Get signed URL and headers
    signed_data = get_signed_url(product_url)
    if not signed_data:
        logging.error("Failed to get signed URL.")
        return None

    signature_obj = signed_data.get("signed_url")
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
        signed_url = signature_obj if isinstance(signature_obj, str) else product_url

    headers = {
        "User-Agent": user_agent,
        "Cookie": cookies,
        "Referer": "https://www.tiktok.com/"
    }

    # Proxy Configuration
    proxies = None
    if os.environ.get("HTTP_PROXY"):
        proxies = {"http": os.environ.get("HTTP_PROXY"), "https": os.environ.get("HTTPS_PROXY")}
    
    try:
        # Use curl_cffi with Chrome impersonation
        # Note: We override User-Agent to match the signature.
        logging.info("Sending request via curl_cffi with impersonate='chrome124'...")
        response = cffi_requests.get(
            signed_url, 
            headers=headers, 
            impersonate="chrome124",
            proxies=proxies,
            timeout=30
        )
        response.raise_for_status()
        
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
        elif "text/html" in content_type:
            # Decode content to string (handle encoding)
            try:
                html_text = response.content.decode('utf-8', errors='ignore')
                return parse_html_for_data(html_text, product_url)
            except Exception as e:
                logging.error(f"Error processing HTML: {e}")
                return None
        else:
            logging.warning(f"Response content type is {content_type}. Might be Protobuf.")
            return None

    except Exception as e:
        logging.error(f"Request failed: {e}")
        return None

def extract_product_info(json_data, product_url):
    try:
        product_data = json_data.get("data", {})
        if not product_data:
            logging.warning("No 'data' field in JSON response.")
            return None

        item = product_data.get("product_info", {})
        
        return {
            "timestamp": datetime.now().isoformat(),
            "url": product_url,
            "product_id": item.get("product_id", "unknown"),
            "total_stock": item.get("stock", 0),
            "total_sold": item.get("sold_count", 0),
            "price": item.get("price", {}).get("min_price", 0),
            "raw_response_snippet": str(json_data)[:200]
        }
    except Exception as e:
        logging.error(f"Error extracting product info: {e}")
        return None

async def monitor_product(url, duration_days=7, interval_hours=1):
    start_time = datetime.now()
    end_time = start_time + timedelta(days=duration_days)
    
    logging.info(f"Starting monitor for: {url}")
    logging.info(f"Duration: {duration_days} days. Interval: {interval_hours} hours.")
    
    try:
        while datetime.now() < end_time:
            current_data = fetch_product_data(url)
            if current_data:
                # Save locally
                with open(MONITOR_LOG_FILE, "a") as f:
                    f.write(json.dumps(current_data) + "\n")
                
                # Push to Apify Dataset if available
                if Actor:
                    await Actor.push_data(current_data)
                
                logging.info(f"Data recorded: {current_data}")
            else:
                logging.warning("No data fetched this interval.")
            
            # Use asyncio sleep if in async context
            await asyncio.sleep(interval_hours * 3600)
            
    except asyncio.CancelledError:
        logging.info("Monitoring cancelled.")
    except KeyboardInterrupt:
        logging.info("Monitoring stopped manually.")
    
    logging.info("Monitoring finished.")

async def main():
    target_url = None
    duration_days = 7
    interval_hours = 1

    if Actor:
        logging.info("Running in Apify Actor environment.")
        await Actor.init()
        
        # Get input
        actor_input = await Actor.get_input() or {}
        logging.info(f"Received input: {actor_input}")
        
        # Parse input
        if "startUrls" in actor_input:
            start_urls = actor_input.get("startUrls", [])
            if start_urls and len(start_urls) > 0:
                # Check structure
                first_url = start_urls[0]
                if isinstance(first_url, dict):
                    target_url = first_url.get("url")
                elif isinstance(first_url, str):
                    target_url = first_url
        
        if not target_url and "url" in actor_input:
             target_url = actor_input.get("url")

        # Check command line args if input didn't provide URL (useful for local testing with Actor lib installed)
        if not target_url and len(sys.argv) > 1:
            target_url = sys.argv[1]
             
        # Override duration/interval if provided
        if "duration_days" in actor_input:
            duration_days = int(actor_input.get("duration_days"))
        if "interval_hours" in actor_input:
            interval_hours = float(actor_input.get("interval_hours"))

    else:
        logging.info("Running in standalone environment.")
        # Command line args fallback
        if len(sys.argv) > 1:
            target_url = sys.argv[1]

    if not target_url:
        logging.error("No target URL provided via input or arguments.")
        if Actor:
            await Actor.fail(status_message="No target URL provided.")
            await Actor.exit()
        sys.exit(1)

    # Run monitoring
    await monitor_product(target_url, duration_days, interval_hours)
    
    if Actor:
        await Actor.exit()

if __name__ == "__main__":
    if Actor:
        asyncio.run(main())
    else:
        # Simple blocking run if no Actor lib (though async def main needs loop)
        asyncio.run(main())
