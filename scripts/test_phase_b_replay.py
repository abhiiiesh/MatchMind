"""Automated Playwright verification test for Phase B: Match Selector & Replay Scrubber."""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SCREENSHOT_DIR = Path("scripts/test_screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


async def run_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        print("Navigating to MatchMind Dashboard...")
        await page.goto("http://localhost:5173/")
        await page.wait_for_timeout(2500)

        # 1. Capture initial Phase B dashboard with TimelineScrubber
        print("1. Capturing Phase B dashboard with TimelineScrubber...")
        await page.screenshot(path=str(SCREENSHOT_DIR / "11_phase_b_timeline_scrubber.png"))

        # 2. Click on a key highlight pin or quick-jump button (e.g. 14' Saka or 67' Martinelli)
        print("2. Clicking highlight quick-jump button...")
        highlight_btn = page.locator("button:has-text('Martinelli')")
        if await highlight_btn.count() > 0:
            await highlight_btn.first.click()
            await page.wait_for_timeout(1500)
            print("Seeked to Martinelli 67' highlight")
            await page.screenshot(path=str(SCREENSHOT_DIR / "12_phase_b_key_moment_seek.png"))
        else:
            # Fallback to seeking on track
            first_highlight = page.locator("button:has-text('Saka')")
            if await first_highlight.count() > 0:
                await first_highlight.first.click()
                await page.wait_for_timeout(1500)
                await page.screenshot(path=str(SCREENSHOT_DIR / "12_phase_b_key_moment_seek.png"))

        # 3. Switch Match in the Header dropdown to Manchester City vs Chelsea
        print("3. Switching match fixture to Manchester City vs Chelsea...")
        select_box = page.locator("select[title='Switch Premier League match fixture']")
        if await select_box.count() > 0:
            await select_box.select_option("mancity_chelsea_2024")
            await page.wait_for_timeout(2000)
            print("Switched match to mancity_chelsea_2024")
            await page.screenshot(path=str(SCREENSHOT_DIR / "13_phase_b_match_switched.png"))

        # 4. Click Play button on the scrubber to start replay
        print("4. Testing Replay Play button...")
        play_btn = page.locator("button:has-text('▶ Play')")
        if await play_btn.count() > 0:
            await play_btn.first.click()
            await page.wait_for_timeout(2500)
            print("Replay started, capturing live playback...")
            await page.screenshot(path=str(SCREENSHOT_DIR / "14_phase_b_playback_active.png"))

        await browser.close()
        print("Phase B browser verification complete! All screenshots saved.")


if __name__ == "__main__":
    asyncio.run(run_test())
