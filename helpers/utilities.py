import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]  # project_root

CREDS_PATH = BASE_DIR / "ignore" / "espn_creds.json"
OWNER_MAP_PATH = BASE_DIR / "ignore" / "owner_map.json"

def get_credentials(path = CREDS_PATH):
    with open(path) as f:
        return json.load(f)


def get_owner_map(path = OWNER_MAP_PATH):
    with open(path) as f:
        return json.load(f)
