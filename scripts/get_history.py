import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from espn_api.football import League
import pandas as pd
from helpers.utilities import get_credentials, get_owner_map

CREDS = get_credentials()
OWNER_MAP = get_owner_map()

# === USER CONFIGURATION ===
LEAGUE_ID = 885349          # Replace with your ESPN league ID
YEAR_RANGE = range(2013, 2026)  # Adjust start/end years as needed
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
    
    team_count = len(league.teams)
    end_of_reg_season = league.settings.reg_season_count
    
    for team in league.teams:
        history_data.append({
            'Year': year,
            'Owner ID': team.team_id,
            'Owner Name': OWNER_MAP.get(str(team.team_id)),
            'Wins': team.wins,
            'Losses': team.losses,
            'Points For': team.points_for,
            'Points Against': team.points_against,
            'Final Standing': team.final_standing,
            'Champion': team.final_standing == 1,
            'Sacko': league.standings_weekly(end_of_reg_season).index(team) + 1 == team_count
        })

# Convert to DataFrame for export or displayf
df = pd.DataFrame(history_data)
df = df.sort_values(by=['Year', 'Final Standing'])

# Display or export
df.to_csv('../league_history.csv', index=False)
