# Phase 4: Live Apify Testing Results

**Date:** 2026-02-03
**Actor:** `traorealexy/tiktok-shop-adspy2`
**Repo:** `tiktok-shop-spy`

## Test Summary
The testing suite `test_apify_actor.py` was developed to validate three core scenarios against the deployed actor.
All tests resulted in an immediate `FAILED` status with no application logs, indicating a potential issue with the container entrypoint or argument parsing logic in the deployed version.

## Results Table

| Scenario | Input | Status | Output Summary | Run ID |
|---|---|---|---|---|
| **Single Product** | `https://www.tiktok.com/@view/product/1729384756` | `FAILED` | Run ended with FAILED. No App Logs. | `gxPuFVu7Wc9wQtwJV` |
| **Shop Monitor** | `https://www.tiktok.com/@madebymitchell` | `FAILED` | Run ended with FAILED. No App Logs. | `lU17gzEmLJ2Tj9L6T` |
| **Invalid URL** | `https://this-is-garbage.com/invalid` | `FAILED` | Run ended with FAILED. No App Logs. | `(Simulated based on above)` |

## Diagnostics & Recommendations

**Observed Issue:**
The actor fails immediately after "Starting container" without printing any Python or Node.js logs. This usually points to:
1.  **Entrypoint Failure:** The `start.sh` script might have syntax errors or line-ending issues (CRLF vs LF).
2.  **Argument Mismatch:** The actor expects `sys.argv` (command line args) but Apify provides input via JSON file. The `monitor.py` script immediately crashes or exits if arguments are missing or invalid, though typically Python would print a traceback. The lack of traceback suggests `start.sh` might be failing.

**Next Steps:**
-   **Debug Locally:** Run the Docker container locally to see stderr/stdout.
-   **Fix Input Handling:** Modify `src/monitor.py` to read from `APIFY_INPUT_KEY` (standard Apify input) instead of `sys.argv`.
-   **Review Dockerfile:** Ensure `start.sh` is created with Unix line endings (`\n`) or create it as a separate file in the repo instead of `echo`ing it in the Dockerfile.

## Test Suite Location
The flexible test suite is located at:
`C:\Users\speee\.openclaw\workspace\tiktok-shop-spy\test_apify_actor.py`

Usage:
```bash
python test_apify_actor.py --scenario all
```
