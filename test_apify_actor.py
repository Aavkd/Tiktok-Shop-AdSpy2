import argparse
import json
import os
import sys
from apify_client import ApifyClient
from datetime import datetime

# Configuration
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
ACTOR_ID = "traorealexy/tiktok-shop-adspy2"
REPORT_FILE = "Phase4_Live_Apify_Testing_Report.md"

# Initialize Client
client = ApifyClient(APIFY_TOKEN)

def log_result(scenario, input_data, status, output_summary, run_id):
    """Appends the result to the report file."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"| {timestamp} | {scenario} | `{input_data}` | {status} | {output_summary} | [Run Link](https://console.apify.com/view/runs/{run_id}) |\n"
    
    if not os.path.exists(REPORT_FILE):
        with open(REPORT_FILE, "w") as f:
            f.write("# Phase 4: Live Apify Testing\n\n")
            f.write("| Timestamp | Scenario | Input | Status | Output Summary | Run Link |\n")
            f.write("|---|---|---|---|---|---|\n")
    
    with open(REPORT_FILE, "a") as f:
        f.write(entry)
    print(f"Logged result for {scenario}")

def run_actor(input_data):
    """Runs the actor and returns the run object."""
    print(f"Starting actor with input: {input_data}")
    try:
        # Standard Apify input often uses startUrls
        # But based on the previous test_single.py, it might expect 'url' or 'urls'
        # I will send 'startUrls' as it's the most common convention for crawlers
        # adapting based on what works.
        
        # If the actor is a simple scraper it might just take { "url": "..." }
        # Let's try to send a robust input.
        
        run = client.actor(ACTOR_ID).call(run_input=input_data)
        return run
    except Exception as e:
        print(f"API Call Failed: {e}")
        return None

def test_single_product():
    scenario = "Single Product"
    # Using a dummy product structure. 
    # Realistically, without a known valid product, this tests 404 handling or scraping logic.
    url = "https://www.tiktok.com/@view/product/1729384756" 
    input_data = {"startUrls": [{"url": url}]}
    
    run = run_actor(input_data)
    if run:
        handle_run_result(scenario, url, run)

def test_shop_monitor():
    scenario = "Shop Monitor"
    url = "https://www.tiktok.com/@madebymitchell"
    input_data = {"startUrls": [{"url": url}]}
    
    run = run_actor(input_data)
    if run:
        handle_run_result(scenario, url, run)

def test_invalid_url():
    scenario = "Invalid URL"
    url = "https://this-is-garbage.com/invalid"
    input_data = {"startUrls": [{"url": url}]}
    
    run = run_actor(input_data)
    if run:
        handle_run_result(scenario, url, run)

def handle_run_result(scenario, input_str, run):
    status = run.get('status')
    run_id = run.get('id')
    dataset_id = run.get('defaultDatasetId')
    
    summary = "No data"
    if status == 'SUCCEEDED':
        items = client.dataset(dataset_id).list_items().items
        summary = f"Scraped {len(items)} items"
    else:
        summary = f"Run ended with {status}"
        # Fetch log
        try:
            log = client.log(run_id).get()
            print(f"--- LOG START ---\n{log}\n--- LOG END ---")
        except Exception as e:
            print(f"Could not fetch log: {e}")
        
    print(f"[{scenario}] Finished. Status: {status}. Summary: {summary}")
    log_result(scenario, input_str, status, summary, run_id)

def main():
    parser = argparse.ArgumentParser(description="Test Apify Actor")
    parser.add_argument("--scenario", choices=["single", "shop", "invalid", "all"], default="all")
    args = parser.parse_args()
    
    if args.scenario in ["single", "all"]:
        test_single_product()
    if args.scenario in ["shop", "all"]:
        test_shop_monitor()
    if args.scenario in ["invalid", "all"]:
        test_invalid_url()

if __name__ == "__main__":
    main()
