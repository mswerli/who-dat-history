import pandas as pd
from collections import defaultdict
from espn_api.football import League
import json

# Load credentials
with open('../ignore/espn_creds.json') as f:
    creds = json.load(f)

league_id = 885349
years = range(2019, 2025)
swid = creds['swid']
espn_s2 = creds['espn_s2']

records = []

player_season_totals = defaultdict(float)  # {(playerId, name, owner): totalPoints}

# Initialize record holders
team_game_high = {"owner": "", "points": 0, "year": 0, "week": 0}
team_game_low = {"owner": "", "points": float('inf'), "year": 0, "week": 0}
player_game_high = {"name": "", "owner": "", "points": 0, "year": 0, "week": 0}
player_game_high_by_pos = {}
team_season_totals = defaultdict(float)

for year in years:
    print(f"Processing {year}...")
    try:
        league = League(league_id=league_id, year=year, swid=swid, espn_s2=espn_s2)
    except Exception as e:
        print(f"Failed to load {year}: {e}")
        continue

    team_id_to_owner = {
        team.team_id: f"{team.owners[0]['firstName'][0]}{team.owners[0]['lastName'][0]}"
        for team in league.teams
    }

    for week in range(1, league.settings.reg_season_count + 1):
        try:
            scoreboard = league.box_scores(week)
        except Exception as e:
            print(f"Failed week {week} in {year}: {e}")
            continue

        for box in scoreboard:
            for team, score in [(box.home_team, box.home_score), (box.away_team, box.away_score)]:
                if not team:
                    continue
                owner = team_id_to_owner.get(team.team_id, "??")
                team_season_totals[owner] += score

                if score > team_game_high["points"]:
                    team_game_high = {"owner": owner, "points": score, "year": year, "week": week}
                if score < team_game_low["points"]:
                    team_game_low = {"owner": owner, "points": score, "year": year, "week": week}

            for side, players in [('home', box.home_lineup), ('away', box.away_lineup)]:
                team_obj = box.home_team if side == 'home' else box.away_team
                owner = team_id_to_owner.get(team_obj.team_id, "??")
                for player in players:
                    if not player.name or player.points is None:
                        continue
                    name = player.name
                    pos = player.position
                    pts = player.points

                    player_season_totals[(player.playerId, name, owner)] += pts

                    if pts > player_game_high["points"]:
                        player_game_high = {
                            "name": name, "owner": owner, "points": pts, "year": year, "week": week
                        }

                    if pos and (pos not in player_game_high_by_pos or pts > player_game_high_by_pos[pos]["points"]):
                        player_game_high_by_pos[pos] = {
                            "name": name, "owner": owner, "points": pts, "year": year, "week": week
                        }

# Team season totals
season_high = max(team_season_totals.items(), key=lambda x: x[1])
season_low = min(team_season_totals.items(), key=lambda x: x[1])

records.extend([
    {"Category": "Team Game", "Record": "Most Points", "Owner": team_game_high["owner"], "Detail": "", "Points": round(team_game_high["points"], 2), "Year": team_game_high["year"], "Week": team_game_high["week"]},
    {"Category": "Team Game", "Record": "Least Points", "Owner": team_game_low["owner"], "Detail": "", "Points": round(team_game_low["points"], 2), "Year": team_game_low["year"], "Week": team_game_low["week"]},
    {"Category": "Team Season", "Record": "Most Points", "Owner": season_high[0], "Detail": "", "Points": round(season_high[1], 2), "Year": "", "Week": ""},
    {"Category": "Team Season", "Record": "Least Points", "Owner": season_low[0], "Detail": "", "Points": round(season_low[1], 2), "Year": "", "Week": ""},
    {"Category": "Single Game", "Record": "Top Player", "Owner": player_game_high["owner"], "Detail": player_game_high["name"], "Points": round(player_game_high["points"], 2), "Year": player_game_high["year"], "Week": player_game_high["week"]}
])

for pos, rec in player_game_high_by_pos.items():
    records.append({
        "Category": "Single Game", "Record": f"Top {pos}", "Owner": rec["owner"], "Detail": rec["name"],
        "Points": round(rec["points"], 2), "Year": rec["year"], "Week": rec["week"]
    })

# Output to CSV
df = pd.DataFrame(records)
output_path = "../all_time_records.csv"
df.to_csv(output_path, index=False)
output_path
