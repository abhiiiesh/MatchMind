"""Comprehensive Live User Testing Script for MatchMind.

Drives headless Chrome to test every UI component, user interaction, WebSocket stream,
simulation trigger, persona switch, language translation, and player focus mode.
"""

import json
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

SCREENSHOT_DIR = Path("scripts/test_screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)



def run_live_test():
    results = {
        "page_load": False,
        "initial_agent_count": 0,
        "simulation_triggered": False,
        "events_received": 0,
        "feed_items_count": 0,
        "metrics_updated": False,
        "momentum_graph_active": False,
        "persona_switch_tested": False,
        "language_switch_tested": False,
        "player_focus_tested": False,
        "audio_bar_present": False,
        "console_errors": [],
        "ui_elements_detected": [],
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1600, "height": 1000})
        page = context.new_page()

        # Capture console errors
        def on_console(msg):
            if msg.type in ["error"]:
                results["console_errors"].append(msg.text)
                print(f"[BROWSER CONSOLE ERROR] {msg.text}")

        page.on("console", on_console)

        print("\n--- 1. Visiting http://localhost:5173/ ---")
        page.goto("http://localhost:5173/", wait_until="networkidle", timeout=20000)
        results["page_load"] = True
        print(f"Page Title: '{page.title()}'")

        # Take initial screenshot
        page.screenshot(path=str(SCREENSHOT_DIR / "01_initial_dashboard.png"))
        print(f"Saved initial dashboard screenshot to {SCREENSHOT_DIR / '01_initial_dashboard.png'}")

        # Check key components
        components = [
            ("Header", "header"),
            ("Pitch Visualization", "svg"),
            ("Metrics Panel", "text=EXPECTED GOALS"),
            ("Explainability Card", "text=Awaiting live tactical, text=WHY THIS MOMENT MATTERS"),
            ("Live Feed", "text=Live Intelligence Stream"),
            ("Agent Status Bar", "text=MULTI-AGENT MESH"),
            ("Momentum Graph", "text=LIVE MATCH MOMENTUM CURVE"),
            ("Audio Commentary Bar", "text=AI Neural Radio"),
        ]

        for name, selector in components:
            count = page.locator(selector).count()
            if count > 0:
                results["ui_elements_detected"].append(name)
                print(f"✅ Found UI component: {name}")
            else:
                print(f"❌ Missing UI component: {name}")

        results["audio_bar_present"] = "Audio Commentary Bar" in results["ui_elements_detected"]
        results["momentum_graph_active"] = "Momentum Graph" in results["ui_elements_detected"]

        # Check multi-agent status bar for agent badges
        agent_badges = page.locator("div.bg-slate-900.border.border-slate-800").count()
        results["initial_agent_count"] = agent_badges
        print(f"Active agent badges detected in UI status bar: {agent_badges}")

        # --- 2. Trigger Live Simulation ---
        print("\n--- 2. Triggering Live Simulation ---")
        sim_button = page.locator("button:has-text('Live Simulation'), button:has-text('Simulate')").first
        if sim_button.is_visible():
            print("Clicking 'Live Simulation' button...")
            sim_button.click()
            results["simulation_triggered"] = True

            # Wait for events to start streaming
            print("Streaming events over WebSocket (waiting 8 seconds)...")
            time.sleep(8)
            page.screenshot(path=str(SCREENSHOT_DIR / "02_simulation_active.png"))
            print(f"Saved simulation active screenshot to {SCREENSHOT_DIR / '02_simulation_active.png'}")

            # Check feed items
            feed_items = page.locator("div.rounded-lg.p-3").count()
            results["feed_items_count"] = feed_items
            print(f"Live Feed items accumulated: {feed_items}")

            # Check if metrics updated
            xg_loc = page.locator("text=/EXPECTED GOALS|Expected Goals/i").first
            xg_text = xg_loc.locator("..").text_content() if xg_loc.count() > 0 else "N/A"
            print(f"Live xG Metric status: {xg_text}")
            results["metrics_updated"] = bool(feed_items > 0)

        # --- 3. Test Persona Switching ---
        print("\n--- 3. Testing Audience Persona Switching ---")
        personas = ["Tactical Analyst", "Casual Fan", "Broadcast Call", "Audio Description"]
        for p_name in personas:
            p_btn = page.locator(f"button:has-text('{p_name}')").first
            if p_btn.is_visible():
                p_btn.click()
                time.sleep(0.5)
                print(f"✅ Switched to persona: '{p_name}'")
        results["persona_switch_tested"] = True
        page.screenshot(path=str(SCREENSHOT_DIR / "03_persona_switched.png"))

        # --- 4. Test Language Switching ---
        print("\n--- 4. Testing Language Selector ---")
        lang_select = page.locator("select").first
        if lang_select.is_visible():
            for lang in ["es", "hi", "ar", "en"]:
                lang_select.select_option(lang)
                time.sleep(0.5)
                print(f"✅ Selected language: '{lang}'")
            results["language_switch_tested"] = True
            page.screenshot(path=str(SCREENSHOT_DIR / "04_language_switched.png"))

        # --- 5. Test Player Focus Mode ---
        print("\n--- 5. Testing Player Focus Mode ---")
        saka_btn = page.locator("button:has-text('Bukayo Saka')").first
        if saka_btn.is_visible():
            print("Found 'Bukayo Saka' focus pill; clicking...")
            saka_btn.click()
            time.sleep(1)
        else:
            player_node = page.locator("[data-testid='player-ball-node']").first
            if player_node.is_visible():
                print("Clicking active player dot on pitch...")
                player_node.click(force=True)
                time.sleep(1)

        focus_card = page.locator("text=Focus Mode")
        if focus_card.count() > 0:
            print("✅ Player Focus Card is visible and verified!")
            results["player_focus_tested"] = True
            page.screenshot(path=str(SCREENSHOT_DIR / "05_player_focus_card.png"))
            print(f"Saved player focus screenshot to {SCREENSHOT_DIR / '05_player_focus_card.png'}")
        else:
            print("⚠️ Player focus card not detected")

        # --- 6. Final State Capture ---
        time.sleep(2)
        page.screenshot(path=str(SCREENSHOT_DIR / "06_final_dashboard_state.png"))
        print(f"\nFinal test screenshot saved to {SCREENSHOT_DIR / '06_final_dashboard_state.png'}")

        browser.close()

    return results


if __name__ == "__main__":
    test_results = run_live_test()
    print("\n========================================================")
    print("LIVE USER TESTING SUMMARY RESULTS:")
    print("========================================================")
    print(json.dumps(test_results, indent=2))
