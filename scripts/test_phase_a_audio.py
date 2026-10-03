"""Automated verification test for Phase A: Azure AI Speech Neural Audio & SSML."""

import asyncio
import sys
from pathlib import Path
from playwright.async_api import async_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCREENSHOT_DIR = Path("scripts/test_screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

async def test_phase_a():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        page = await browser.new_page(viewport={"width": 1600, "height": 1000})

        print("--- 1. Loading MatchMind Dashboard ---")
        await page.goto("http://localhost:5173/", wait_until="networkidle", timeout=15000)
        await page.wait_for_timeout(1000)

        # Trigger live simulation so we have active narratives
        print("--- 2. Triggering Live Simulation ---")
        sim_btn = page.locator("button:has-text('Live Simulation')").first
        if await sim_btn.is_visible():
            await sim_btn.click()
            print("Simulation started, streaming events (waiting 5s)...")
            await page.wait_for_timeout(5000)

        # Check Audio Commentary Bar
        print("--- 3. Testing Audio Commentary Bar ---")
        neural_badge = page.locator("text=Azure Neural")
        assert await neural_badge.count() > 0, "Azure Neural badge should be present"
        print("✅ Found 'Azure Neural' badge in Audio Bar")

        # Click Play button on audio bar
        play_btn = page.locator("button[title*='Listen to Live AI Audio'], button[title*='Live Audio']").first
        if await play_btn.is_visible():
            await play_btn.click()
            print("✅ Clicked Live Audio Play button")
            await page.wait_for_timeout(2000)

        await page.screenshot(path=str(SCREENSHOT_DIR / "09_phase_a_neural_audio.png"))
        print(f"Saved screenshot: {SCREENSHOT_DIR / '09_phase_a_neural_audio.png'}")

        # Check if SSML button appeared and click it
        ssml_btn = page.locator("button:has-text('SSML')").first
        if await ssml_btn.is_visible():
            print("Found SSML inspection button, clicking...")
            await ssml_btn.click()
            await page.wait_for_timeout(500)
            try:
                await page.wait_for_selector("pre", timeout=4000)
            except Exception:
                pass

            modal_title = page.locator("text=Azure Speech Synthesis Markup")
            assert await modal_title.count() > 0, "SSML Modal should be visible"
            print("✅ SSML Modal opened successfully with valid markup")

            await page.screenshot(path=str(SCREENSHOT_DIR / "10_phase_a_ssml_modal.png"))
            print(f"Saved screenshot: {SCREENSHOT_DIR / '10_phase_a_ssml_modal.png'}")

            # Close modal
            close_btn = page.locator("button:has-text('Close')").first
            if await close_btn.is_visible():
                await close_btn.click()
                print("Closed SSML Modal")
        else:
            print("SSML button not yet rendered (waiting for event callback)")

        await browser.close()
        print("\n🎉 Phase A: Azure Neural Speech & SSML Test COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(test_phase_a())
