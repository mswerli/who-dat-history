import json
import pandas as pd
from espn_api.football import League

# Load credentials
with open('../ignore/espn_creds.json') as f:
    creds = json.load(f)

# Load updated payout configuration
with open('weekly_payouts_config.json') as f:
    payouts_config = json.load(f)["weekly_payouts"]

league_id = 885349
year = 2024
swid = creds['swid']
espn_s2 = creds['espn_s2']

league = League(league_id, year, espn_s2=espn_s2, swid=swid)

# Map team_id to owner initials
team_id_to_owner = {
    team.team_id: f"{team.owners[0]['firstName'][0]}{team.owners[0]['lastName'][0]}"
    for team in league.teams
}

winners = []

for week_str, payout in payouts_config.items():
    week = int(week_str)
    scoreboard = league.box_scores(week)

    winner_entry = {"Week": week, "Award": payout["type"], "Winner": "", "Players": [], "Total Points": 0}

    if payout["type"] == "highest_total_points":
        top_score = 0
        for box in scoreboard:
            for team, score in [(box.home_team, box.home_score), (box.away_team, box.away_score)]:
                if score > top_score:
                    top_score = score
                    winner_entry.update({
                        "Award": "Highest Total Points",
                        "Winner": team_id_to_owner.get(team.team_id, team.team_name),
                        "Players": [],
                        "Total Points": score
                    })

    elif payout["type"] == "top_slot":
        top_score = 0
        slots_needed = payout["slots"]
        for box in scoreboard:
            for team, lineup in [(box.home_team, box.home_lineup), (box.away_team, box.away_lineup)]:
                selected_players = []
                valid_lineup = True
                for slot, count in slots_needed.items():
                    eligible_players = [p for p in lineup if p.slot_position == slot]
                    eligible_players.sort(key=lambda p: p.points, reverse=True)
                    if len(eligible_players) < count:
                        valid_lineup = False
                        break
                    selected_players.extend(eligible_players[:count])

                if not valid_lineup:
                    continue

                total_points = sum(p.points for p in selected_players)
                if total_points > top_score:
                    top_score = total_points
                    winner_entry.update({
                        "Award": f"Top {' & '.join([f'{k} ({v})' for k,v in slots_needed.items()])}",
                        "Winner": team_id_to_owner.get(team.team_id, team.team_name),
                        "Players": [{"Name": p.name, "Points": p.points, "Slot": p.slot_position} for p in selected_players],
                        "Total Points": total_points
                    })

    elif payout["type"] == "top_player_overall":
        top_player = None
        top_score = 0
        for box in scoreboard:
            for team, lineup in [(box.home_team, box.home_lineup), (box.away_team, box.away_lineup)]:
                starters = [p for p in lineup if p.slot_position not in ["BE", "IR"]]
                for player in starters:
                    if player.points > top_score:
                        top_score = player.points
                        top_player = player
                        winner_entry.update({
                            "Award": "Top Overall Player",
                            "Winner": team_id_to_owner.get(team.team_id, team.team_name),
                            "Players": [{"Name": player.name, "Points": player.points, "Slot": player.slot_position}],
                            "Total Points": player.points
                        })

    elif payout["type"] == "top_slot_combo":
        top_score = 0
        slots_needed = payout["slots"]
        for box in scoreboard:
            for team, lineup in [(box.home_team, box.home_lineup), (box.away_team, box.away_lineup)]:
                selected_players = []
                valid_combo = True
                for slot, count in slots_needed.items():
                    eligible_players = [p for p in lineup if p.slot_position == slot]
                    eligible_players.sort(key=lambda p: p.points, reverse=True)
                    if len(eligible_players) < count:
                        valid_combo = False
                        break
                    selected_players.extend(eligible_players[:count])

                if not valid_combo:
                    continue

                total_points = sum(p.points for p in selected_players)
                if total_points > top_score:
                    top_score = total_points
                    winner_entry.update({
                        "Award": f"Top {' & '.join(slots_needed.keys())} Combo",
                        "Winner": team_id_to_owner.get(team.team_id, team.team_name),
                        "Players": [{"Name": p.name, "Points": p.points, "Slot": p.slot_position} for p in selected_players],
                        "Total Points": total_points
                    })

    if winner_entry["Winner"]:
        winners.append(winner_entry)

# Create CSV
output_rows = []
for w in winners:
    output_rows.append({
        "Week": w["Week"],
        "Award": w["Award"],
        "Winner": w["Winner"],
        "Players": "; ".join(f"{p['Name']} ({p['Slot']}: {p['Points']})" for p in w["Players"]),
        "Total Points": w["Total Points"]
    })

df = pd.DataFrame(output_rows)
output_path = "../weekly_payout_winners.csv"
df.to_csv(output_path, index=False)

output_path
