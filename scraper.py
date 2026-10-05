import os
import asyncio
from playwright.async_api import async_playwright

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "data", "raw_pdfs")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Verified, direct PDF document endpoints on LIC's server
PDF_TARGETS = {
    "LIC_Jeevan_Labh_Brochure.pdf": "https://licindia.in/documents/20121/1243952/LIC_Jeevan+labh_Sales+Brochure_4+inch+x+9+inch_Eng.pdf",
    "LIC_Jeevan_Utsav_Brochure.pdf": "https://licindia.in/documents/20121/1319704/Sales+Brochure_LICs+Jeevan+Utsav.pdf",
    "LIC_Amritbaal_Brochure.pdf": "https://licindia.in/documents/20121/1319704/Sales+Brochure_LICs_Amritbaal.pdf",
    "LIC_New_Pension_Plus_Brochure.pdf": "https://licindia.in/documents/20121/1319704/Sales+Brochure_LICs_New_Pension_Plus.pdf"
}

async def download_direct_pdfs():
    async with async_playwright() as p:
        print("Launching Chromium request context...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
        )

        for filename, url in PDF_TARGETS.items():
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            print(f"\nDownloading: {filename}")
            try:
                # Issue HTTP request directly through Playwright browser context
                response = await context.request.get(url, timeout=30000)
                
                if response.status == 200:
                    body = await response.body()
                    with open(filepath, "wb") as f:
                        f.write(body)
                    print(f"  Successfully saved ({len(body) // 1024} KB) -> {filepath}")
                else:
                    print(f"  Failed with HTTP Status: {response.status}")

            except Exception as e:
                print(f"  Error downloading {filename}: {e}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(download_direct_pdfs())