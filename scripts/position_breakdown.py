from espn_api.football import League
from collections import defaultdict
import pandas as pd
import json

# === CONFIGURATION ===
CREDS_FILE = '../ignore/espn_creds.json'
with open(CREDS_FILE) as f:
    CREDS = json.load(f)

LEAGUE_ID = 885349  # Replace with your league ID
YEAR_RANGE = range(2013, 2025)
SWID = CREDS['swid']
ESPN_S2 = CREDS['espn_s2']

VALID_POSITIONS = ['QB', 'RB', 'WR', 'TE', 'K', 'D/ST']

# === ACCUMULATORS ===
stats = defaultdict(lambda: defaultdict(float))  # (owner_id, year) -> {position: points}
total_points = defaultdict(float)                # (owner_id, year) -> total points
owner_names = {}                                 # owner_id -> initials

for year in YEAR_RANGE:
    print(f"Processing {year}...")
    try:
        league = League(league_id=LEAGUE_ID, year=year, swid=SWID, espn_s2=ESPN_S2)
    except Exception as e:
        print(f"  Failed to load league for {year}: {e}")
        continue

    # Map team_id to owner_id and initials
    team_owner_map = {}
    for team in league.teams:
        try:
            owner_id = team.owners[0]['id']
            initials = f"{team.owners[0]['firstName'][0]}{team.owners[0]['lastName'][0]}"
            team_owner_map[team.team_id] = owner_id
            owner_names[owner_id] = initials
        except Exception:
            continue  # skip malformed team

    # Get all weeks from settings.matchup_periods
    try:
        week_numbers = sorted(int(w) for w in league.settings.matchup_periods.keys())
    except Exception as e:
        print(f"  Could not retrieve matchup weeks for {year}: {e}")
        continue

    for week in week_numbers:
        try:
            box_scores = league.box_scores(week)
        except Exception as e:
            print(f"    Error loading week {week}: {e}")
            continue

        for box in box_scores:
            for side in ['home', 'away']:
                team = getattr(box, f"{side}_team")
                lineup = getattr(box, f"{side}_lineup")

                owner_id = team_owner_map.get(team.team_id)
                if not owner_id:
                    continue

                for player in lineup:
                    if player.slot_position not in VALID_POSITIONS:
                        continue  # only starters

                    points = player.points or 0
                    pos = player.position
                    pos = "D/ST" if pos in ["DEF", "D/ST"] else pos

                    if pos in VALID_POSITIONS:
                        stats[(owner_id, year)][pos] += points
                        total_points[(owner_id, year)] += points

# === BUILD OUTPUT ===
rows = []
for (owner_id, year), pos_breakdown in stats.items():
    total = total_points[(owner_id, year)]
    row = {
        "Owner ID": owner_id,
        "Owner Name": owner_names.get(owner_id, "??"),
        "Year": year,
        "Total Points": round(total, 2)
    }
    for pos in VALID_POSITIONS:
        pct = (pos_breakdown[pos] / total) * 100 if total > 0 else 0
        row[f"{pos} %"] = round(pct, 2)
    rows.append(row)

# === EXPORT ===
if rows:
    df = pd.DataFrame(rows)
    df = df.sort_values(by=["Year", "Owner Name"])
    df.to_csv("../positional_contributions.csv", index=False)
    print("Saved to ../positional_contributions.csv")
else:
    print("No data collected. Nothing to write.")
