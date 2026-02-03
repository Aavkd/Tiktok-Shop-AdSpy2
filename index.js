const express = require('express');
const { addExtra } = require('puppeteer-extra');
const puppeteerCore = require('puppeteer-core');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');

const puppeteer = addExtra(puppeteerCore);
puppeteer.use(StealthPlugin());

const app = express();
app.use(express.json());

const PORT = 8081;
let browser;
let page;

async function initBrowser() {
    console.log('Launching browser...');
    browser = await puppeteer.launch({
        executablePath: "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        headless: "new",
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu'
        ]
    });
    page = await browser.newPage();
    
    // Set a realistic User Agent (Stealth plugin handles this usually, but explicit is good)
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36');

    console.log('Navigating to TikTok to load signing scripts...');
    // We need to visit a page that loads the signer. The main page usually works.
    await page.goto('https://www.tiktok.com/?is_from_webapp=1&sender_device=pc', {
        waitUntil: 'networkidle2',
        timeout: 60000
    });

    // Check if signer is available
    const signerAvailable = await page.evaluate(() => {
        return typeof window.byted_acrawler !== 'undefined';
    });

    if (signerAvailable) {
        console.log('Signer (byted_acrawler) found!');
    } else {
        console.error('Signer NOT found. Reloading might be needed.');
    }
}

app.post('/signature', async (req, res) => {
    const { url } = req.body;
    if (!url) {
        return res.status(400).json({ status: 'error', message: 'URL is required' });
    }

    try {
        if (!page) {
             await initBrowser();
        }

        // Inspect byted_acrawler
        const inspection = await page.evaluate(() => {
            if (typeof window.byted_acrawler === 'undefined') return "undefined";
            
            // Get keys
            const keys = Object.keys(window.byted_acrawler);
            // Get types
            const types = {};
            keys.forEach(k => types[k] = typeof window.byted_acrawler[k]);
            return { keys, types };
        });
        console.log("Inspector:", inspection);

        const signature = await page.evaluate((targetUrl) => {
            if (typeof window.byted_acrawler === 'undefined') return null;
            
            try {
                // Try frontierSign. It might take just the URL string or an object.
                // Usually frontierSign returns the signature object directly.
                // Let's try passing the object {url: targetUrl}
                if (typeof window.byted_acrawler.frontierSign === 'function') {
                    return window.byted_acrawler.frontierSign({
                        "X-Bogus": true // enable bogus?
                    }, {
                         url: targetUrl
                    });
                }
                
                // Fallback or retry
                return { error: "No signing function found" };
            } catch (e) {
                // If the first signature fails, try just the URL string
                 try {
                    return window.byted_acrawler.frontierSign(targetUrl);
                } catch (e2) {
                     return { error: e.toString() + " | " + e2.toString() };
                }
            }
        }, url);

        if (!signature) {
             return res.status(500).json({ status: 'error', message: 'Signer not available or failed' });
        }
        
        // Capture cookies and UA to ensure consistency
        const cookies = await page.cookies();
        const cookieString = cookies.map(c => `${c.name}=${c.value}`).join('; ');
        const ua = await page.evaluate(() => navigator.userAgent);

        res.json({
            status: 'ok',
            data: {
                signed_url: signature, // If it returns the full URL or params
                signature_data: signature, // Raw object
                cookies: cookieString,
                navigator: {
                    user_agent: ua
                }
            }
        });

    } catch (error) {
        console.error('Error signing:', error);
        res.status(500).json({ status: 'error', message: error.toString() });
    }
});

app.listen(PORT, async () => {
    console.log(`Signature service running on port ${PORT}`);
    await initBrowser();
});
