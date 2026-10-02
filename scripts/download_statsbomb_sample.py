"""StatsBomb Open Data Sample Match Downloader."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from data.synthetic.statsbomb_adapter import StatsBombStreamer
from statsbombpy import sb

def main():
    print("Listing available free competitions from StatsBomb Open Data...")
    try:
        comps = sb.competitions()
        print(f"Found {len(comps)} available competitions.")
        # Print a few top competitions (e.g. Premier League, Champions League, World Cup)
        top_comps = comps[['competition_id', 'season_id', 'country_name', 'competition_name', 'season_name']].head(10)
        print(top_comps.to_string(index=False))

        # Test loading sample match (default match)
        print("\nLoading sample match events...")
        streamer = StatsBombStreamer(match_id="3869685")
        events = streamer.get_events()
        print(f"Successfully loaded and parsed {len(events)} events for match 3869685.")
        if events:
            first_event = events[0]
            print(f"First event: {first_event.event_type} by {first_event.team.name} at {first_event.timestamp}")
            shots = [e for e in events if e.event_type == "Shot"]
            print(f"Total shots in match: {len(shots)}")
    except Exception as exc:
        print(f"Note: StatsBomb API live fetch: {exc}")
        print("Falling back to local synthetic generator mode.")

if __name__ == "__main__":
    main()
