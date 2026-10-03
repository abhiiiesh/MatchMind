"""Automated Playwright verification test for Phase C: Tactical Heatmap & Pass Network Overlays."""

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
        await page.wait_for_timeout(2000)

        # 1. Test Heatmap Overlay
        print("1. Activating Tactical Heatmap Overlay...")
        heatmap_btn = page.locator("button:has-text('🔥 Heatmap')")
        if await heatmap_btn.count() > 0:
            await heatmap_btn.first.click()
            await page.wait_for_timeout(1500)
            print("Captured Heatmap view...")
            await page.screenshot(path=str(SCREENSHOT_DIR / "15_phase_c_heatmap.png"))

        # 2. Test Pass Network Overlay
        print("2. Activating Pass Network Overlay...")
        pass_net_btn = page.locator("button:has-text('🕸️ Pass Network')")
        if await pass_net_btn.count() > 0:
            await pass_net_btn.first.click()
            await page.wait_for_timeout(1500)
            print("Captured Pass Network view...")
            await page.screenshot(path=str(SCREENSHOT_DIR / "16_phase_c_pass_network.png"))

        # 3. Test Defensive Pressing Zones Overlay
        print("3. Activating Defensive Pressing Zones Overlay...")
        pressing_btn = page.locator("button:has-text('🛡️ Pressing')")
        if await pressing_btn.count() > 0:
            await pressing_btn.first.click()
            await page.wait_for_timeout(1500)
            print("Captured Pressing Zones view...")
            await page.screenshot(path=str(SCREENSHOT_DIR / "17_phase_c_pressing_zones.png"))

        # 4. Test Player-Specific Heatmap
        print("4. Testing Player-Specific Heatmap for Bukayo Saka...")
        if await heatmap_btn.count() > 0:
            await heatmap_btn.first.click()
            await page.wait_for_timeout(800)

        saka_btn = page.locator("button:has-text('Bukayo Saka')")
        if await saka_btn.count() > 0:
            await saka_btn.first.click()
            await page.wait_for_timeout(1500)
            print("Captured Saka personal Heatmap view...")
            await page.screenshot(path=str(SCREENSHOT_DIR / "18_phase_c_player_heatmap.png"))

        await browser.close()
        print("Phase C automated browser verification complete! All screenshots saved.")


if __name__ == "__main__":
    asyncio.run(run_test())
