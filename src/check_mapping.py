import yaml
import pathlib

# PATH RESOLUTION
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parent
YAML_PATH = ROOT_DIR / "wild_data" / "data.yaml"

if not YAML_PATH.exists():
    raise FileNotFoundError(f"Could not locate data.yaml at {YAML_PATH}")

# Load the 64-class configuration
with open(YAML_PATH, 'r') as f:
    data = yaml.safe_load(f)

raw_names = data['names']

# 0:glass, 1:metal, 2:paper, 3:plastic, 4:trash
MAPPING = {
    4: 0, 20: 0, 21: 0, 22: 0, 23: 0,
    0: 1, 1: 1, 2: 1, 12: 1, 17: 1, 26: 1, 27: 1, 28: 1, 49: 1, 51: 1,
    8: 2, 13: 2, 14: 2, 24: 2, 25: 2, 29: 2, 30: 2, 36: 2, 37: 2, 38: 2, 39: 2, 40: 2, 58: 2, 59: 2, 63: 2,
    7: 3, 9: 3, 10: 3, 11: 3, 15: 3, 16: 3, 19: 3, 31: 3, 32: 3, 33: 3, 34: 3, 35: 3,
    41: 3, 42: 3, 43: 3, 44: 3, 45: 3, 46: 3, 47: 3, 48: 3, 53: 3, 54: 3, 55: 3, 56: 3, 60: 3,
    3: 4, 5: 4, 6: 4, 18: 4, 50: 4, 52: 4, 57: 4, 61: 4, 62: 4
}

# Group raw classes by target MIRA IDs
mira_groups = {0: [], 1: [], 2: [], 3: [], 4: []}
mira_names = {0: "GLASS", 1: "METAL", 2: "PAPER", 3: "PLASTIC", 4: "TRASH (REJECT)"}

for raw_id, raw_name in enumerate(raw_names):
    if raw_id in MAPPING:
        target_id = MAPPING[raw_id]
        mira_groups[target_id].append((raw_id, raw_name))

# Print Audit Report
print("=" * 60)
print("MIRA DATASET MAPPING AUDIT REPORT")
print("=" * 60)

for target_id, items in mira_groups.items():
    print(f"\nTarget Class [{target_id}]: {mira_names[target_id]}")
    print("-" * 40)
    for raw_id, raw_name in items:
        print(f"  Mapped index {raw_id:<2} -> {raw_name}")

print("\n" + "=" * 60)
print("Unmapped classes (These will be automatically ignored):")
print("=" * 60)
for raw_id, raw_name in enumerate(raw_names):
    if raw_id not in MAPPING:
        print(f"  Ignored index {raw_id:<2} -> {raw_name}")