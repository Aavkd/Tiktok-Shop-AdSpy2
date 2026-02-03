import requests
import sys

def test_stealth():
    url = "http://localhost:8081/signature"
    target_url = "https://www.tiktok.com/@shop/product/example"
    try:
        print(f"Calling {url} with {target_url}...")
        resp = requests.post(url, json={"url": target_url})
        if resp.status_code != 200:
            print(f"FAILED: Status {resp.status_code}, {resp.text}")
            sys.exit(1)
        
        data = resp.json()
        if data.get("status") != "ok":
            print(f"FAILED: Status not ok: {data.get('status')}")
            sys.exit(1)
            
        payload = data.get("data", {})
        signed_url = payload.get("signed_url")
        cookies = payload.get("cookies")
        ua = payload.get("navigator", {}).get("user_agent")
        
        print("Response received:")
        # print(payload) # Verbose

        # Verify X-Bogus
        if isinstance(signed_url, dict):
            bogus = signed_url.get("X-Bogus")
            if bogus:
                print(f"SUCCESS: X-Bogus found: {bogus}")
            else:
                print("FAILED: X-Bogus missing in signature object")
                sys.exit(1)
        else:
            # Maybe it returns full URL
            if "X-Bogus" in str(signed_url):
                 print(f"SUCCESS: X-Bogus found in URL string: {signed_url[:50]}...")
            else:
                 print("FAILED: X-Bogus missing in signed URL string")
                 sys.exit(1)

        # Verify Cookies
        if cookies:
            print(f"SUCCESS: Cookies captured ({len(cookies)} chars)")
        else:
            print("WARNING: No cookies captured")

        # Verify User Agent
        if "HeadlessChrome" in ua:
             print(f"FAILED: User Agent contains HeadlessChrome: {ua}")
             sys.exit(1)
        else:
             print(f"SUCCESS: User Agent looks legit: {ua}")

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_stealth()
