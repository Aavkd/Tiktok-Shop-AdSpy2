# Monitor Mode Design

## Objective
Track a specific TikTok Shop product URL for 7 days to analyze sales trends and stock depletion.

## Workflow

1.  **Input Parsing**
    *   Accept a raw TikTok Shop product URL.
    *   Extract the `product_id` and `shop_id` from the URL via regex or initial HTTP GET (ignoring hydration for now).

2.  **Data Acquisition Loop**
    *   **Frequency**: Every 1 hour (configurable).
    *   **Duration**: 7 days (168 hours).
    *   **Request**:
        *   Generate `X-Bogus`/`X-Gnarly` signature for the product detail API endpoint.
        *   Send GET request with valid headers.
    *   **Extraction**:
        *   Current Price (`price.min_price`, `price.max_price`).
        *   Stock Level (`stock_infos` - often requires summing SKU level stock).
        *   Sales Count (`sold_count` - usually cumulative, so calculate delta for hourly sales).

3.  **Data Storage**
    *   Format: JSON Lines (`.jsonl`) or SQLite.
    *   Schema:
        ```json
        {
          "timestamp": "2023-10-27T10:00:00Z",
          "product_id": "172938471",
          "total_stock": 150,
          "total_sold": 5420,
          "price": 29.99
        }
        ```

4.  **Reporting**
    *   At the end of 7 days (or on demand), generate a simple CSV report showing:
        *   Sales per hour/day.
        *   Stock depletion rate.
        *   Revenue estimation (Price * Sales Delta).

## Technical Requirements
*   **Signature Service**: Must be reliable. If signatures fail, the monitor will gap.
*   **Proxies**: Rotating proxies might be needed to avoid 7-day IP bans, though low frequency (1/hr) might survive on residential IP.
