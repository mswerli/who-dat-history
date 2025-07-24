from espn_api.football import League
import pandas as pd
import json
from collections import defaultdict

# === Configuration ===
CREDS_FILE = '../ignore/espn_creds.json'
LEAGUE_ID = 885349
YEAR_RANGE = range(2013, 2025)  # Adjust as needed

# === Load credentials ===
with open(CREDS_FILE) as f:
    CREDS = json.load(f)

SWID = CREDS['swid']
ESPN_S2 = CREDS['espn_s2']

# === Matchup tracker ===
matchups = defaultdict(lambda: {
    'Wins': 0, 'Losses': 0, 'Ties': 0,
    'Games Played': 0,
    'Points For': 0.0,
    'Points Against': 0.0
})

# === Map owner_id to latest name ===
owner_id_to_name = {}

for year in YEAR_RANGE:
    print(f"Processing {year}...")
    try:
        league = League(league_id=LEAGUE_ID, year=year, swid=SWID, espn_s2=ESPN_S2)
    except Exception as e:
        print(f"Error loading {year}: {e}")
        continue

    team_map = {team.team_id: team for team in league.teams}
    id_map = {team.team_id: team.owners[0]['id'] for team in league.teams}
    name_map = {team.owners[0]['id']: f"{team.owners[0]['firstName'][0]}{team.owners[0]['lastName'][0]}" for team in league.teams}
    owner_id_to_name.update(name_map)

    for week in range(1, league.settings.reg_season_count + 1):
        scoreboard = league.scoreboard(week)
        for match in scoreboard:
            if not match.home_team or not match.away_team:
                continue

            home_id = id_map[match.home_team.team_id]
            away_id = id_map[match.away_team.team_id]

            home_points = match.home_score
            away_points = match.away_score

            # Track for both perspectives
            for p1, p2, p1_pts, p2_pts in [
                (home_id, away_id, home_points, away_points),
                (away_id, home_id, away_points, home_points)
            ]:
                key = (p1, p2)
                matchups[key]['Games Played'] += 1
                matchups[key]['Points For'] += p1_pts
                matchups[key]['Points Against'] += p2_pts

                if p1_pts > p2_pts:
                    matchups[key]['Wins'] += 1
                elif p1_pts < p2_pts:
                    matchups[key]['Losses'] += 1
                else:
                    matchups[key]['Ties'] += 1

# === Build output DataFrame ===
records = []
for (owner_id, opp_id), stats in matchups.items():
    records.append({
        'Owner ID': owner_id,
        'Owner Name': owner_id_to_name.get(owner_id, 'Unknown'),
        'Opponent ID': opp_id,
        'Opponent Name': owner_id_to_name.get(opp_id, 'Unknown'),
        'Win %': round(100 * stats['Wins'] / stats['Games Played'], 2) if stats['Games Played'] > 0 else 0.0,
        **stats
    })

df = pd.DataFrame(records)

# Optional: sort and format
df = df.sort_values(by=['Owner Name', 'Opponent Name'])
df.to_csv('../head_to_head_lifetime.csv', index=False)