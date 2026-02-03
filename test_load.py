import requests
import time
import concurrent.futures

SERVICE_URL = "http://localhost:8081/signature"
TEST_URL = "https://www.tiktok.com/api/product/detail?productId=123456789"

def send_request(i):
    try:
        start = time.time()
        resp = requests.post(SERVICE_URL, json={"url": TEST_URL}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        duration = time.time() - start
        if data.get("status") == "ok":
            return True, duration
        else:
            return False, duration
    except Exception as e:
        return False, 0

def load_test(total_requests=50, concurrency=5):
    print(f"Starting load test: {total_requests} requests, concurrency {concurrency}")
    success_count = 0
    total_time = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(send_request, i) for i in range(total_requests)]
        
        for future in concurrent.futures.as_completed(futures):
            success, duration = future.result()
            if success:
                success_count += 1
                total_time += duration
            else:
                print("Request failed")

    avg_time = total_time / success_count if success_count > 0 else 0
    print(f"Load test finished. Success: {success_count}/{total_requests}. Avg Time: {avg_time:.4f}s")

if __name__ == "__main__":
    load_test()
