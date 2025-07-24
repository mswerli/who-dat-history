from espn_api.football import League
from collections import defaultdict
import json
import pandas as pd

# Load credentials
with open('../ignore/espn_creds.json') as f:
    creds = json.load(f)

league_id = 885349
years = range(2019, 2025)
swid = creds['swid']
espn_s2 = creds['espn_s2']

records = []

player_season_totals = defaultdict(lambda: defaultdict(float))  # {year: {(playerId, name, owner): totalPoints}}

for year in years:
    print(f"Processing {year}...")
    try:
        league = League(league_id=league_id, year=year, swid=swid, espn_s2=espn_s2)
    except Exception as e:
        print(f"Failed to load {year}: {e}")
        continue

    team_totals = defaultdict(float)
    team_id_to_owner = {
        team.team_id: f"{team.owners[0]['firstName'][0]}{team.owners[0]['lastName'][0]}"
        for team in league.teams
    }

    team_game_high = {"owner": "", "points": 0, "year": 0, "week": 0}
    team_game_low = {"owner": "", "points": float('inf'), "year": 0, "week": 0}
    player_game_high = {"name": "", "owner": "", "points": 0, "year": 0, "week": 0}
    player_game_high_by_pos = {}

    for week in range(1, league.settings.reg_season_count + 1):
        try:
            scoreboard = league.box_scores(week)
        except Exception as e:
            print(f"Failed week {week} in {year}: {e}")
            continue

        for box in scoreboard:
            for team in [box.home_team, box.away_team]:
                if not team:
                    continue
                owner = team_id_to_owner.get(team.team_id, "??")
                points = box.home_score if team == box.home_team else box.away_score
                team_totals[owner] += points

                if points > team_game_high["points"]:
                    team_game_high = {"owner": owner, "points": points, "year": year, "week": week}
                if points < team_game_low["points"]:
                    team_game_low = {"owner": owner, "points": points, "year": year, "week": week}

            for side, players in [('home', box.home_lineup), ('away', box.away_lineup)]:
                team_obj = box.home_team if side == 'home' else box.away_team
                owner = team_id_to_owner.get(team_obj.team_id, "??")
                for player in players:
                    if not player.name or player.points is None:
                        continue
                    name = player.name
                    pos = player.position
                    pts = player.points

                    player_season_totals[year][(player.playerId, name, owner)] += pts

                    if pts > player_game_high["points"]:
                        player_game_high = {
                            "name": name, "owner": owner, "points": pts, "year": year, "week": week
                        }

                    if pos and (pos not in player_game_high_by_pos or pts > player_game_high_by_pos[pos]["points"]):
                        player_game_high_by_pos[pos] = {
                            "name": name, "owner": owner, "points": pts, "year": year, "week": week
                        }

    season_high = max(team_totals.items(), key=lambda x: x[1])
    season_low = min(team_totals.items(), key=lambda x: x[1])

    records.extend([
        {"Category": "Most Points (Team Game)", "Owner": team_game_high["owner"], "Detail": "", "Points": round(team_game_high["points"], 2), "Year": team_game_high["year"], "Week": team_game_high["week"]},
        {"Category": "Least Points (Team Game)", "Owner": team_game_low["owner"], "Detail": "", "Points": round(team_game_low["points"], 2), "Year": team_game_low["year"], "Week": team_game_low["week"]},
        {"Category": "Most Points (Team Season)", "Owner": season_high[0], "Detail": "", "Points": round(season_high[1], 2), "Year": year, "Week": ""},
        {"Category": "Least Points (Team Season)", "Owner": season_low[0], "Detail": "", "Points": round(season_low[1], 2), "Year": year, "Week": ""},
        {"Category": "Top Player (Single Game)", "Owner": player_game_high["owner"], "Detail": player_game_high["name"], "Points": round(player_game_high["points"], 2), "Year": player_game_high["year"], "Week": player_game_high["week"]}
    ])

    for pos, rec in player_game_high_by_pos.items():
        records.append({
            "Category": f"Top {pos} (Single Game)", "Owner": rec["owner"], "Detail": rec["name"],
            "Points": round(rec["points"], 2), "Year": rec["year"], "Week": rec["week"]
        })

# Highest scoring player in a season
top_player_season = {"points": 0}
for year, players in player_season_totals.items():
    for (pid, name, owner), total in players.items():
        if total > top_player_season.get("points", 0):
            top_player_season = {
                "name": name, "owner": owner, "points": total, "year": year
            }

records.append({
    "Category": "Top Player (Season)", "Owner": top_player_season["owner"],
    "Detail": top_player_season["name"], "Points": round(top_player_season["points"], 2),
    "Year": top_player_season["year"], "Week": ""
})

# Output to CSV
df = pd.DataFrame(records)
df.to_csv("../all_time_records.csv", index=False)
print("✅ Records saved to data/all_time_records.csv")
