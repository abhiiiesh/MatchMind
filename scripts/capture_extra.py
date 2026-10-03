import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCREENSHOT_DIR = Path("scripts/test_screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        
        # 1. Capture OBS Overlay
        page_obs = await browser.new_page(viewport={"width": 1920, "height": 1080})
        await page_obs.goto("http://localhost:8000/overlay?match_id=match_demo_01&persona=tactical_analyst&lang=en")
        await page_obs.wait_for_timeout(2000)
        await page_obs.screenshot(path=str(SCREENSHOT_DIR / "07_obs_overlay.png"))
        print(f"✅ Saved OBS overlay screenshot to {SCREENSHOT_DIR / '07_obs_overlay.png'}")
        await page_obs.close()

        # 2. Capture Spanish Live Translation Stream
        page_ui = await browser.new_page(viewport={"width": 1600, "height": 1000})
        await page_ui.goto("http://localhost:5173/")
        await page_ui.wait_for_timeout(1500)
        await page_ui.locator("select").first.select_option("es")
        await page_ui.wait_for_timeout(500)
        sim_btn = page_ui.locator("button:has-text('Live Simulation')").first
        if await sim_btn.is_visible():
            await sim_btn.click()
            print("Triggered simulation for Spanish localization test...")
            await page_ui.wait_for_timeout(6000)
            await page_ui.screenshot(path=str(SCREENSHOT_DIR / "08_spanish_live_stream.png"))
            print(f"✅ Saved Spanish screenshot to {SCREENSHOT_DIR / '08_spanish_live_stream.png'}")
        await page_ui.close()

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
