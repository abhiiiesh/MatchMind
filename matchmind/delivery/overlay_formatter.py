"""Broadcast Overlay Formatter for MatchMind.

Formats explainable match intelligence into machine-readable JSON and
HTML5 templates optimized for OBS Studio, CasparCG, and vMix.
"""

from typing import Any, Dict


class BroadcastOverlayFormatter:
    """Formats live match events into lower-third and side-panel graphics payloads."""

    @staticmethod
    def format_lower_third(payload: Dict[str, Any], persona: str = "broadcast_commentator") -> Dict[str, Any]:
        narrative = payload.get("narrative", {})
        metric_state = payload.get("metric_state", {})
        event = payload.get("event", {})
        commentary_map = narrative.get("commentary_by_persona", {})

        score = metric_state.get("score", {"home": 0, "away": 0})
        commentary_text = commentary_map.get(persona) or commentary_map.get("broadcast_commentator", "")

        return {
            "template": "premier_league_lower_third",
            "minute": metric_state.get("minute", 0),
            "match_clock": f"{metric_state.get('minute', 0):02d}'",
            "home_team": metric_state.get("home_team", "Home"),
            "away_team": metric_state.get("away_team", "Away"),
            "score": f"{score.get('home', 0)} - {score.get('away', 0)}",
            "story_arc": narrative.get("game_state_arc", "Live Match"),
            "commentary": commentary_text,
            "why_it_matters": narrative.get("why_it_matters_explanation", ""),
            "stats_ticker": {
                "xg_home": f"{metric_state.get('cumulative_xg', {}).get('home', 0.0):.2f}",
                "xg_away": f"{metric_state.get('cumulative_xg', {}).get('away', 0.0):.2f}",
                "field_tilt": f"{metric_state.get('field_tilt', 50.0):.1f}%",
                "home_ppda": f"{metric_state.get('rolling_ppda', {}).get('home', 11.5):.1f}",
            },
            "is_goal": (event.get("outcome") == "Goal"),
            "is_high_leverage": (narrative.get("leverage_index", 1.0) >= 3.0),
        }

    @staticmethod
    def render_overlay_html(match_id: str, persona: str = "casual_fan", lang: str = "en") -> str:
        """Returns a self-contained transparent HTML page suitable for OBS Studio Browser Source."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>MatchMind Broadcast Overlay</title>
  <style>
    body {{
      margin: 0;
      padding: 0;
      background: transparent;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      overflow: hidden;
      color: #fff;
    }}
    #overlay-container {{
      position: absolute;
      bottom: 24px;
      left: 32px;
      right: 32px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .banner {{
      background: linear-gradient(135deg, rgba(20, 20, 35, 0.94), rgba(45, 15, 60, 0.94));
      border-left: 6px solid #00ff87;
      border-radius: 8px;
      padding: 12px 20px;
      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
      display: flex;
      align-items: center;
      justify-content: space-between;
      backdrop-filter: blur(8px);
    }}
    .score-badge {{
      display: flex;
      align-items: center;
      gap: 14px;
      font-size: 20px;
      font-weight: 800;
      letter-spacing: 0.5px;
    }}
    .clock {{
      background: #38003c;
      color: #00ff87;
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 16px;
    }}
    .narrative-box {{
      font-size: 15px;
      color: #f0f0f5;
      max-width: 60%;
      line-height: 1.4;
    }}
    .metrics-pills {{
      display: flex;
      gap: 10px;
      font-size: 13px;
    }}
    .pill {{
      background: rgba(255, 255, 255, 0.12);
      padding: 4px 10px;
      border-radius: 12px;
      font-weight: 600;
    }}
    .why-it-matters {{
      background: rgba(0, 255, 135, 0.15);
      border: 1px solid rgba(0, 255, 135, 0.4);
      color: #d1ffd6;
      border-radius: 6px;
      padding: 8px 16px;
      font-size: 13px;
      animation: fadeIn 0.4s ease-out;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(6px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
  </style>
</head>
<body>
  <div id="overlay-container">
    <div class="why-it-matters" id="why-box">
      ⚡ <b>MatchMind AI:</b> Connecting to real-time intelligence feed...
    </div>
    <div class="banner">
      <div class="score-badge">
        <span class="clock" id="clock">00'</span>
        <span id="teams">Match Starting</span>
        <span id="score" style="color: #00ff87;">0 - 0</span>
      </div>
      <div class="narrative-box" id="commentary">
        Awaiting live match events...
      </div>
      <div class="metrics-pills">
        <div class="pill" id="xg-pill">xG: 0.0 - 0.0</div>
        <div class="pill" id="tilt-pill">Field Tilt: 50%</div>
      </div>
    </div>
  </div>

  <script>
    const matchId = "{match_id}";
    const persona = "{persona}";
    const lang = "{lang}";
    const wsUrl = `ws://${{window.location.host}}/ws/match/${{matchId}}?persona=${{persona}}&lang=${{lang}}`;
    
    function connect() {{
      const ws = new WebSocket(wsUrl);
      ws.onmessage = (event) => {{
        const msg = JSON.parse(event.data);
        if (msg.message_type === "VERIFIED_OUTPUT") {{
          const p = msg.payload;
          const n = p.narrative || {{}};
          const ms = p.metric_state || {{}};
          const score = ms.score || {{ home: 0, away: 0 }};
          
          document.getElementById("clock").innerText = `${{ms.minute || 0}}'`;
          document.getElementById("teams").innerText = `${{ms.home_team || 'Home'}} vs ${{ms.away_team || 'Away'}}`;
          document.getElementById("score").innerText = `${{score.home}} - ${{score.away}}`;
          
          const commentaryText = (n.translations && n.translations[lang]) 
            ? n.translations[lang] 
            : (n.commentary_by_persona && n.commentary_by_persona[persona]) || "";
          
          document.getElementById("commentary").innerText = commentaryText;
          document.getElementById("why-box").innerHTML = `💡 <b>Why It Matters:</b> ${{n.why_it_matters_explanation || ''}}`;
          
          const xgHome = (ms.cumulative_xg && ms.cumulative_xg.home) ? ms.cumulative_xg.home.toFixed(2) : "0.00";
          const xgAway = (ms.cumulative_xg && ms.cumulative_xg.away) ? ms.cumulative_xg.away.toFixed(2) : "0.00";
          document.getElementById("xg-pill").innerText = `xG: ${{xgHome}} - ${{xgAway}}`;
          document.getElementById("tilt-pill").innerText = `Field Tilt: ${{ms.field_tilt || 50}}%`;
        }}
      }};
      ws.onclose = () => setTimeout(connect, 2000);
    }}
    connect();
  </script>
</body>
</html>"""
