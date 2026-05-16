import json
import os

base = os.path.dirname(os.path.dirname(__file__))
josaa_path = os.path.join(base, "data", "colleges_josaa.json")

with open(josaa_path, encoding='utf-8') as f:
    data = json.load(f)

# Check NITs with jee_advanced
nits_advanced = [c for c in data if 'NIT' in c['name'] and c.get('rank_type') == 'jee_advanced']
print(f"\n=== NITs marked as jee_advanced: {len(nits_advanced)} ===")
for c in nits_advanced[:10]:
    print(f"{c['name']} - {c['branch']} - rank_type: {c['rank_type']}")

# Check IITs with jee_main
iits_main = [c for c in data if 'IIT' in c['name'] and c.get('rank_type') == 'jee_main']
print(f"\n=== IITs marked as jee_main: {len(iits_main)} ===")
for c in iits_main[:10]:
    print(f"{c['name']} - {c['branch']} - rank_type: {c['rank_type']}")

# Summary
print(f"\n=== Summary ===")
print(f"Total colleges: {len(data)}")
print(f"JEE Advanced: {len([c for c in data if c.get('rank_type') == 'jee_advanced'])}")
print(f"JEE Main: {len([c for c in data if c.get('rank_type') == 'jee_main'])}")
