# TikTok Shop Spy (AdSpy 2.0)

**Uncover winning products before your competitors do.**

TikTok Shop Spy tracks product sales, revenue, and stock levels over time, giving you the data-driven edge to find high-potential products before they go viral. Stop guessing and start validating with real-time market data.

---

## ⚡ Key Features

| Feature | Description |
| :--- | :--- |
| **🕵️ Stealth Mode** | Bypasses Akamai and TikTok fingerprinting using a custom Puppeteer stealth service. No more blocked requests. |
| **📉 7-Day Monitor** | Tracks stock variance hourly to estimate real sales volume. Visualizes trends over a 7-day window. |
| **⚡ Hybrid Architecture** | Combines the raw speed of **Node.js** (for signatures & browser automation) with the data crunching power of **Python**. |
| **🧩 Auto-Sig Generation** | automatically generates `X-Bogus`, `X-Gnarly`, and `MsToken` parameters for seamless API access. |
| **📝 JSONL Logging** | Structured, efficient logging for massive datasets, ready for analysis. |

---

## 🛠️ How It Works

TikTok Shop Spy uses a **microservice architecture** to handle the complexity of modern anti-scraping protections.

### The Hybrid Engine
Most scrapers fail because they can't generate valid signatures or get blocked by bot detection. We solved this by splitting the workload:

1.  **Local Microservice (Port 8081):** A lightweight Node.js service runs in the background. It handles the heavy lifting of browser fingerprinting and signature generation (stealth implementation).
2.  **Python Logic:** The core application logic runs in Python, querying the local microservice for valid signatures and then communicating directly with TikTok's API endpoints.

### 🔄 The Workflow
1.  **Target:** You provide a product or shop ID.
2.  **Sign:** Python requests a signature from the Node.js service.
3.  **Fetch:** The request is sent to TikTok with legitimate browser headers.
4.  **Track:** Data is logged and monitored hourly to detect stock changes (sales).

---

## 🏗️ Technical Specs

- **Local Port:** 8081 (Internal Signing Service)
- **Languages:** Python 3.10+ / Node.js 18+
- **Data Format:** JSONL (NewLine Delimited JSON)
- **Status:** 🚧 **Active Development** (Phases 1-3 Complete: Core, Monitor, Stealth)

---

## 🚀 Getting Started

### Prerequisites
- Node.js & npm installed
- Python 3.10+ installed

### Installation

1.  **Clone the repo:**
    ```bash
    git clone https://github.com/Aavkd/Tiktok-Shop-AdSpy2.git
    cd Tiktok-Shop-AdSpy2
    ```

2.  **Install Dependencies (Python):**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Dependencies (Node.js):**
    ```bash
    cd signer_service
    npm install
    ```

4.  **Run:**
    *   Start the signer service: `node signer_service/server.js`
    *   Run the monitor: `python main.py`

---

## ⚠️ Disclaimer

**For Educational Purposes Only.**
This tool is designed to demonstrate web scraping and data analysis techniques. The authors are not responsible for any misuse of this software or any violations of TikTok's Terms of Service. Use responsibly.
