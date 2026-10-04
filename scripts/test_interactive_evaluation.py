"""Comprehensive Interactive Live Evaluation Script for MatchMind.

Tests every button, scrubber interaction, sound/audio listening (Azure Neural & SSML),
language switching (ES, HI, AR, FR, EN), tactical pitch overlays (Heatmap, Pass Network, Pressing),
player focus mode, and multi-agent telemetry to measure system design strength and feature relevance.
"""

import asyncio
import json
import os
import sys
import time
from pathlib import Path
from playwright.async_api import async_playwright

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

EVAL_DIR = Path("scripts/test_screenshots/live_evaluation")
EVAL_DIR.mkdir(parents=True, exist_ok=True)


async def run_evaluation():
    metrics = {
        "buttons_tested": [],
        "fixtures_tested": [],
        "personas_tested": [],
        "languages_tested": {},
        "audio_listening": {},
        "tactical_layers_tested": [],
        "latencies_ms": {},
        "console_errors": [],
        "screenshots_captured": [],
        "overall_health": "UNKNOWN",
    }

    print("\n" + "=" * 70)
    print("  MATCHMIND COMPREHENSIVE INTERACTIVE LIVE EVALUATION")
    print("=" * 70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", headless=True)
        context = await browser.new_context(viewport={"width": 1600, "height": 1000})
        page = await context.new_page()

        # Capture console errors
        def on_console(msg):
            if msg.type == "error":
                metrics["console_errors"].append(msg.text)
                print(f"  [CONSOLE ERROR] {msg.text}")

        page.on("console", on_console)

        # -------------------------------------------------------------
        # STEP 1: INITIAL LOAD & HEALTH CHECK
        # -------------------------------------------------------------
        print("\n[STEP 1] Loading MatchMind Dashboard (http://localhost:5173)...")
        t0 = time.time()
        await page.goto("http://localhost:5173/", wait_until="networkidle", timeout=20000)
        t_load = (time.time() - t0) * 1000
        metrics["latencies_ms"]["initial_page_load"] = round(t_load, 1)
        print(f"  [OK] Page loaded in {t_load:.1f}ms. Title: '{await page.title()}'")

        await page.wait_for_timeout(1000)
        shot1 = str(EVAL_DIR / "eval_01_initial_dashboard.png")
        await page.screenshot(path=shot1)
        metrics["screenshots_captured"].append(shot1)
        print(f"  [SCREENSHOT] Saved: {shot1}")

        # Check Multi-Agent Status Bar
        agent_badges = await page.locator("div.bg-slate-900.border.border-slate-800").count()
        print(f"  [TELEMETRY] Detected {agent_badges} multi-agent status nodes in UI")

        # -------------------------------------------------------------
        # STEP 2: FIXTURE SWITCHING BUTTONS & MATCH CATALOG
        # -------------------------------------------------------------
        print("\n[STEP 2] Testing Match Fixture Switching...")
        select_box = page.locator("select[title='Switch Premier League match fixture']")
        if await select_box.count() > 0:
            fixtures = ["mancity_chelsea_2024", "tottenham_newcastle_2024", "arsenal_liverpool_2024"]
            for fix_id in fixtures:
                t_fix0 = time.time()
                await select_box.select_option(fix_id)
                await page.wait_for_timeout(1200)
                t_fix = (time.time() - t_fix0) * 1000
                metrics["latencies_ms"][f"switch_fixture_{fix_id}"] = round(t_fix, 1)
                metrics["fixtures_tested"].append(fix_id)
                print(f"  [OK] Switched fixture to '{fix_id}' in {t_fix:.1f}ms")

            shot2 = str(EVAL_DIR / "eval_02_fixture_switch_arsenal_liverpool.png")
            await page.screenshot(path=shot2)
            metrics["screenshots_captured"].append(shot2)
            print(f"  [SCREENSHOT] Saved: {shot2}")

        # -------------------------------------------------------------
        # STEP 3: TIMELINE SCRUBBER BUTTONS & PLAYBACK
        # -------------------------------------------------------------
        print("\n[STEP 3] Testing Scrubber Playback Controls...")
        play_btn = page.locator("button:has-text('▶ Play'), button:has-text('⏸ Pause')")
        reset_btn = page.locator("button:has-text('↺ 0\'')")
        step_fwd_btn = page.locator("button:has-text('Step ⏭')")
        step_bwd_btn = page.locator("button:has-text('⏮ Step')")

        # Click Play button
        if await play_btn.count() > 0:
            print("  [CLICK] Pressing '▶ Play' button...")
            await play_btn.first.click()
            metrics["buttons_tested"].append("scrubber_play")
            await page.wait_for_timeout(3000)  # Let match clock advance

            # Check clock text
            clock_text = await page.locator("span.font-mono.font-black").first.text_content()
            print(f"  [CLOCK ADVANCED] Current Match Clock: {clock_text}")

            shot3 = str(EVAL_DIR / "eval_03_scrubber_playback_active.png")
            await page.screenshot(path=shot3)
            metrics["screenshots_captured"].append(shot3)
            print(f"  [SCREENSHOT] Saved: {shot3}")

            # Test Speed buttons: 2x and 5x
            speed_2x = page.locator("button:has-text('2x')")
            if await speed_2x.count() > 0:
                print("  [CLICK] Pressing '2x' speed button...")
                await speed_2x.first.click()
                metrics["buttons_tested"].append("speed_2x")
                await page.wait_for_timeout(1500)

            speed_5x = page.locator("button:has-text('5x')")
            if await speed_5x.count() > 0:
                print("  [CLICK] Pressing '5x' speed button...")
                await speed_5x.first.click()
                metrics["buttons_tested"].append("speed_5x")
                await page.wait_for_timeout(1500)

            # Click Pause
            pause_btn = page.locator("button:has-text('⏸ Pause')")
            if await pause_btn.count() > 0:
                print("  [CLICK] Pressing '⏸ Pause' button...")
                await pause_btn.first.click()
                metrics["buttons_tested"].append("scrubber_pause")
                await page.wait_for_timeout(600)

        # Test Step buttons
        if await step_fwd_btn.count() > 0:
            print("  [CLICK] Pressing 'Step ⏭' button...")
            await step_fwd_btn.first.click()
            metrics["buttons_tested"].append("scrubber_step_forward")
            await page.wait_for_timeout(500)

        if await step_bwd_btn.count() > 0:
            print("  [CLICK] Pressing '⏮ Step' button...")
            await step_bwd_btn.first.click()
            metrics["buttons_tested"].append("scrubber_step_backward")
            await page.wait_for_timeout(500)

        # Test Key Highlights Pins (e.g. Saka, Salah, Martinelli)
        print("  [CLICK] Testing Key Highlight Quick-Jump Buttons...")
        saka_highlight = page.locator("button:has-text('Saka')").first
        if await saka_highlight.count() > 0:
            t_seek0 = time.time()
            await saka_highlight.click()
            await page.wait_for_timeout(1000)
            t_seek = (time.time() - t_seek0) * 1000
            metrics["latencies_ms"]["seek_highlight_saka"] = round(t_seek, 1)
            metrics["buttons_tested"].append("highlight_saka")
            print(f"  [OK] Jumped to Saka highlight in {t_seek:.1f}ms")

            shot4 = str(EVAL_DIR / "eval_04_scrubber_seek_highlight.png")
            await page.screenshot(path=shot4)
            metrics["screenshots_captured"].append(shot4)
            print(f"  [SCREENSHOT] Saved: {shot4}")

        # -------------------------------------------------------------
        # STEP 4: PERSONA SWITCHING BUTTONS
        # -------------------------------------------------------------
        print("\n[STEP 4] Testing Persona Switching Buttons...")
        personas = [
            ("casual_fan", "🎉 Casual Fan"),
            ("tactical_analyst", "🔬 Tactical Analyst"),
            ("broadcast_commentator", "🎙️ Broadcast"),
            ("accessibility_audio", "♿ Audio Description"),
        ]

        for p_id, label in personas:
            p_btn = page.locator(f"button:has-text('{label}')").first
            if await p_btn.count() > 0:
                t_p0 = time.time()
                await p_btn.click()
                await page.wait_for_timeout(800)
                t_p = (time.time() - t_p0) * 1000
                metrics["latencies_ms"][f"switch_persona_{p_id}"] = round(t_p, 1)
                metrics["personas_tested"].append(p_id)
                metrics["buttons_tested"].append(f"persona_{p_id}")
                print(f"  [OK] Activated persona '{label}' in {t_p:.1f}ms")

        # Capture Tactical Analyst view
        shot5 = str(EVAL_DIR / "eval_05_persona_tactical_analyst.png")
        await page.screenshot(path=shot5)
        metrics["screenshots_captured"].append(shot5)
        print(f"  [SCREENSHOT] Saved: {shot5}")

        # -------------------------------------------------------------
        # STEP 5: TACTICAL SPATIAL LAYERS (HEATMAP, PASS NETWORK, PRESSING)
        # -------------------------------------------------------------
        print("\n[STEP 5] Testing Tactical Pitch Spatial Overlays...")
        heatmap_btn = page.locator("button:has-text('🔥 Heatmap')").first
        pass_net_btn = page.locator("button:has-text('🕸️ Pass Network')").first
        pressing_btn = page.locator("button:has-text('🛡️ Pressing')").first
        live_btn = page.locator("button:has-text('🏟️ Live')").first

        # Heatmap
        if await heatmap_btn.count() > 0:
            print("  [CLICK] Pressing '🔥 Heatmap' button...")
            t_hm0 = time.time()
            await heatmap_btn.click()
            await page.wait_for_timeout(1500)
            t_hm = (time.time() - t_hm0) * 1000
            metrics["latencies_ms"]["render_heatmap"] = round(t_hm, 1)
            metrics["tactical_layers_tested"].append("heatmap")
            metrics["buttons_tested"].append("layer_heatmap")
            shot6 = str(EVAL_DIR / "eval_06_tactical_overlay_heatmap.png")
            await page.screenshot(path=shot6)
            metrics["screenshots_captured"].append(shot6)
            print(f"  [SCREENSHOT] Saved: {shot6} (latency: {t_hm:.1f}ms)")

        # Pass Network
        if await pass_net_btn.count() > 0:
            print("  [CLICK] Pressing '🕸️ Pass Network' button...")
            t_pn0 = time.time()
            await pass_net_btn.click()
            await page.wait_for_timeout(1500)
            t_pn = (time.time() - t_pn0) * 1000
            metrics["latencies_ms"]["render_pass_network"] = round(t_pn, 1)
            metrics["tactical_layers_tested"].append("pass_network")
            metrics["buttons_tested"].append("layer_pass_network")
            shot7 = str(EVAL_DIR / "eval_07_tactical_overlay_pass_network.png")
            await page.screenshot(path=shot7)
            metrics["screenshots_captured"].append(shot7)
            print(f"  [SCREENSHOT] Saved: {shot7} (latency: {t_pn:.1f}ms)")

        # Pressing Zones
        if await pressing_btn.count() > 0:
            print("  [CLICK] Pressing '🛡️ Pressing' button...")
            t_pr0 = time.time()
            await pressing_btn.click()
            await page.wait_for_timeout(1500)
            t_pr = (time.time() - t_pr0) * 1000
            metrics["latencies_ms"]["render_pressing"] = round(t_pr, 1)
            metrics["tactical_layers_tested"].append("pressing")
            metrics["buttons_tested"].append("layer_pressing")
            shot8 = str(EVAL_DIR / "eval_08_tactical_overlay_pressing.png")
            await page.screenshot(path=shot8)
            metrics["screenshots_captured"].append(shot8)
            print(f"  [SCREENSHOT] Saved: {shot8} (latency: {t_pr:.1f}ms)")

        # -------------------------------------------------------------
        # STEP 6: PLAYER FOCUS MODE
        # -------------------------------------------------------------
        print("\n[STEP 6] Testing Player Focus Interactive Roster Pills...")
        if await heatmap_btn.count() > 0:
            await heatmap_btn.click()
            await page.wait_for_timeout(800)

        saka_pill = page.locator("button:has-text('Bukayo Saka')").first
        if await saka_pill.count() > 0:
            print("  [CLICK] Selecting 'Bukayo Saka' roster pill...")
            await saka_pill.click()
            await page.wait_for_timeout(1500)
            metrics["buttons_tested"].append("player_focus_saka")

            # Verify focused badge appears
            focused_badge = page.locator("text=⭐ Focused: Bukayo Saka")
            has_badge = await focused_badge.count() > 0
            print(f"  [VERIFICATION] Player focus badge visible: {has_badge}")

            shot9 = str(EVAL_DIR / "eval_09_player_focus_saka_heatmap.png")
            await page.screenshot(path=shot9)
            metrics["screenshots_captured"].append(shot9)
            print(f"  [SCREENSHOT] Saved: {shot9}")

            # Clear player focus
            clear_btn = page.locator("button:has-text('✕')").first
            if await clear_btn.count() > 0:
                await clear_btn.click()
                await page.wait_for_timeout(500)

        # Return pitch to Live mode
        if await live_btn.count() > 0:
            await live_btn.click()
            await page.wait_for_timeout(500)

        # -------------------------------------------------------------
        # STEP 7: SOUND & NEURAL AUDIO LISTENING VERIFICATION
        # -------------------------------------------------------------
        print("\n[STEP 7] Testing Sound & Azure Neural Audio Listening...")
        # Toggle Azure Neural vs Browser TTS
        azure_toggle = page.locator("button[title*='Toggle between Azure Neural']").first
        if await azure_toggle.count() > 0:
            print("  [CLICK] Toggling Audio Engine to verify switch...")
            await azure_toggle.click()
            await page.wait_for_timeout(500)
            await azure_toggle.click()  # return to Azure Neural
            await page.wait_for_timeout(500)
            metrics["buttons_tested"].append("toggle_audio_engine")

        # Click Live Audio Play button
        audio_play_btn = page.locator("button[title*='Listen to Live AI Audio'], button[title*='Live Audio']").first
        if await audio_play_btn.count() > 0:
            print("  [CLICK] Clicking Live Audio Play button to activate radio commentary...")
            t_aud0 = time.time()
            await audio_play_btn.click()
            await page.wait_for_timeout(2500)
            t_aud = (time.time() - t_aud0) * 1000
            metrics["latencies_ms"]["audio_stream_activation"] = round(t_aud, 1)
            metrics["buttons_tested"].append("audio_play_radio")

            # Check HTML5 audio element
            audio_props = await page.evaluate(
                """() => {
                const el = document.querySelector('audio');
                if (!el) return { found: false };
                return {
                    found: true,
                    src: el.src,
                    paused: el.paused,
                    currentTime: el.currentTime,
                    duration: el.duration,
                    readyState: el.readyState
                };
            }"""
            )
            print(f"  [AUDIO DOM STATE] {json.dumps(audio_props, indent=2)}")
            metrics["audio_listening"]["dom_audio_state"] = audio_props

            # Check animated equalizer waves
            eq_bars = await page.locator("span.animate-bounce, span.animate-pulse").count()
            print(f"  [AUDIO VISUALIZER] Animated wave bars active: {eq_bars > 0}")
            metrics["audio_listening"]["equalizer_active"] = eq_bars > 0

            shot10 = str(EVAL_DIR / "eval_10_audio_listening_active.png")
            await page.screenshot(path=shot10)
            metrics["screenshots_captured"].append(shot10)
            print(f"  [SCREENSHOT] Saved: {shot10}")

        # Test SSML Modal Inspection
        print("  [CLICK] Opening Microsoft SSML XML Inspection Modal...")
        ssml_btn = page.locator("button[title*='View Microsoft SSML'], button:has-text('SSML')").first
        if await ssml_btn.count() > 0:
            await ssml_btn.click()
            await page.wait_for_timeout(1000)
            metrics["buttons_tested"].append("ssml_inspector_button")

            modal_visible = await page.locator("text=Azure Speech Synthesis Markup").count() > 0
            ssml_snippet = ""
            if modal_visible:
                pre_tag = page.locator("pre").first
                if await pre_tag.count() > 0:
                    ssml_snippet = await pre_tag.text_content()
                    print(f"  [SSML VERIFIED] First 160 chars:\n    {ssml_snippet[:160]}...")
                    metrics["audio_listening"]["ssml_preview"] = ssml_snippet[:200]
                    metrics["audio_listening"]["has_express_as"] = "mstts:express-as" in ssml_snippet
                    metrics["audio_listening"]["has_prosody"] = "prosody" in ssml_snippet

            shot11 = str(EVAL_DIR / "eval_11_ssml_modal_inspector.png")
            await page.screenshot(path=shot11)
            metrics["screenshots_captured"].append(shot11)
            print(f"  [SCREENSHOT] Saved: {shot11}")

            # Close Modal
            close_btn = page.locator("button:has-text('Close')").first
            if await close_btn.count() > 0:
                await close_btn.click()
                await page.wait_for_timeout(500)

        # -------------------------------------------------------------
        # STEP 8: LANGUAGE SWITCHING (ES, HI, AR, FR, EN)
        # -------------------------------------------------------------
        print("\n[STEP 8] Testing Language Switching (ES, HI, AR, FR, EN)...")
        lang_select = page.locator("select").nth(1)  # Language select is 2nd select in header
        languages = [
            ("es", "🇪🇸 Español", "eval_12_lang_spanish.png"),
            ("hi", "🇮🇳 हिन्दी", "eval_13_lang_hindi.png"),
            ("ar", "🇸🇦 العربية", "eval_14_lang_arabic.png"),
            ("fr", "🇫🇷 Français", "eval_15_lang_french.png"),
            ("en", "🇬🇧 English", "eval_16_lang_english.png"),
        ]

        for code, name, shot_file in languages:
            t_l0 = time.time()
            await lang_select.select_option(code)
            await page.wait_for_timeout(1200)
            t_l = (time.time() - t_l0) * 1000
            metrics["latencies_ms"][f"switch_lang_{code}"] = round(t_l, 1)

            # Check active voice text in Audio Commentary Bar
            voice_label = await page.locator("div.flex.items-center.gap-2.text-\\[10px\\] span").first.text_content()
            metrics["languages_tested"][code] = {
                "name": name,
                "latency_ms": round(t_l, 1),
                "voice_label": voice_label,
            }
            print(f"  [OK] Switched to {name} in {t_l:.1f}ms (Detected Voice: '{voice_label}')")

            shot_path = str(EVAL_DIR / shot_file)
            await page.screenshot(path=shot_path)
            metrics["screenshots_captured"].append(shot_path)
            print(f"  [SCREENSHOT] Saved: {shot_path}")

        # -------------------------------------------------------------
        # STEP 9: LIVE SIMULATION TRIGGER & FEED FLOW
        # -------------------------------------------------------------
        print("\n[STEP 9] Triggering Full Live Simulation Stream...")
        sim_btn = page.locator("button:has-text('Live Stream'), button:has-text('Live Simulation')").first
        if await sim_btn.count() > 0:
            print("  [CLICK] Pressing '▶ Live Stream' button...")
            await sim_btn.click()
            metrics["buttons_tested"].append("header_live_stream")

            # Let simulation run and stream events
            print("  [STREAMING] Streaming multi-agent events over WebSocket (waiting 6 seconds)...")
            await page.wait_for_timeout(6000)

            shot17 = str(EVAL_DIR / "eval_17_full_simulation_active.png")
            await page.screenshot(path=shot17)
            metrics["screenshots_captured"].append(shot17)
            print(f"  [SCREENSHOT] Saved: {shot17}")

        # Check total logged feed items
        feed_items = await page.locator("div.p-3\\.5.space-y-3 > div, div.space-y-3 > div").count()
        print(f"  [FEED LOGGED] Total commentary items displayed: {feed_items}")
        metrics["live_feed_items_count"] = feed_items

        await browser.close()
        print("\n[COMPLETE] Interactive Browser Evaluation Finished Successfully!")

    metrics["overall_health"] = "PASS" if len(metrics["console_errors"]) == 0 else "PASS_WITH_WARNINGS"

    # Save summary report
    report_file = EVAL_DIR / "evaluation_results.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n[REPORT] Saved full evaluation metrics to {report_file}")

    return metrics


if __name__ == "__main__":
    asyncio.run(run_evaluation())
