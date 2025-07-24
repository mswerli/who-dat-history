from espn_api.football import League
import pandas as pd
import json


CREDS_FILE = '../ignore/espn_creds.json'

with open(CREDS_FILE) as f:
    CREDS = json.load(f)

# === USER CONFIGURATION ===
LEAGUE_ID = 885349          # Replace with your ESPN league ID
YEAR_RANGE = range(2013, 2024)  # Adjust start/end years as needed
SWID = CREDS['swid']       # Copy this from your browser cookies
ESPN_S2 = CREDS['espn_s2']    # Copy this from your browser cookies

# === MAIN SCRIPT ===
history_data = []

for year in YEAR_RANGE:
    print(f"Fetching data for {year}...")
    try:
        league = League(league_id=LEAGUE_ID, year=year, swid=SWID, espn_s2=ESPN_S2)
    except Exception as e:
        print(f"Error loading year {year}: {e}")
        continue
    
    for team in league.teams:
        history_data.append({
            'Year': year,
            'Team': team.team_name,
            'Owner ID': team.owners[0]['id'],
            'Owner Name': f"{team.owners[0]['firstName'][0]}{team.owners[0]['lastName'][0]}",
            'Wins': team.wins,
            'Losses': team.losses,
            'Points For': team.points_for,
            'Points Against': team.points_against,
            'Final Standing': team.final_standing
        })

# Convert to DataFrame for export or display
df = pd.DataFrame(history_data)
df = df.sort_values(by=['Year', 'Final Standing'])

# Display or export
df.to_csv('../league_history.csv', index=False)
