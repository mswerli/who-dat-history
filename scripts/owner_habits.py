from espn_api.football import League
import pandas as pd
import json
from collections import defaultdict, Counter

# === LOAD CREDENTIALS ===
CREDS_FILE = '../ignore/espn_creds.json'
with open(CREDS_FILE) as f:
    CREDS = json.load(f)

# === CONFIGURATION ===
LEAGUE_ID = 885349               # Replace with your league ID
YEAR_RANGE = range(2013, 2026)
SWID = CREDS['swid']
ESPN_S2 = CREDS['espn_s2']

# === ACCUMULATORS ===
owner_player_counts = defaultdict(Counter)
owner_player_years = defaultdict(lambda: defaultdict(list))  # owner_id -> player_name -> [years]
owner_initials = {}

# === MAIN LOOP ===
for year in YEAR_RANGE:
    print(f"Processing {year}...")
    try:
        league = League(league_id=LEAGUE_ID, year=year, swid=SWID, espn_s2=ESPN_S2)
    except Exception as e:
        print(f"Failed to load league for {year}: {e}")
        continue

    team_id_to_owner = {}
    for team in league.teams:
        if not team.owners or not team.owners[0].get('id'):
            continue
        owner_id = team.owners[0]['id']
        initials = f"{team.owners[0]['firstName'][0]}{team.owners[0]['lastName'][0]}"
        team_id_to_owner[team.team_id] = owner_id
        owner_initials[owner_id] = initials

    try:
        draft = league.draft
    except Exception as e:
        print(f"Could not load draft data for {year}: {e}")
        continue

    for pick in draft:
        team = pick.team
        player_name = pick.playerName
        if team.team_id not in team_id_to_owner:
            continue
        owner_id = team_id_to_owner[team.team_id]
        owner_player_counts[owner_id][player_name] += 1
        owner_player_years[owner_id][player_name].append(year)

# === OUTPUT ===
rows = []
for owner_id, counter in owner_player_counts.items():
    if not counter:
        continue
    top_player, count = counter.most_common(1)[0]
    seasons = sorted(owner_player_years[owner_id][top_player])
    rows.append({
        "Owner ID": owner_id,
        "Owner Name": owner_initials.get(owner_id, "??"),
        "Most Drafted Player": top_player,
        "Times Drafted": count,
        "Drafted Seasons": " / ".join(map(str, seasons)) 
    })

df = pd.DataFrame(rows)
df = df.sort_values(by="Times Drafted", ascending=False)
df.to_csv("../most_drafted_players.csv", index=False)
print("Exported to ../most_drafted_players.csv")
